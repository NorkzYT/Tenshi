package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/chromedp/chromedp"
)

// ChapterInfo defines the structure of a chapter as extracted by our scripts.
type ChapterInfo struct {
	Title  string  `json:"title"`
	Number float64 `json:"number"`
	URL    string  `json:"url"`
}

// ChapterImages defines the structure for the JSON response from the /get_image endpoint.
type ChapterImages struct {
	Chapter string   `json:"chapter"`
	Images  []string `json:"images"`
}

// JavaScript snippets used for extraction.
const (
	// jsTitle extracts the series title.
	jsTitle = `document.querySelector("div.post-title h1") ? document.querySelector("div.post-title h1").innerText : "";`

	// jsChapters extracts the list of chapters.
	jsChapters = `(function(){
		var chapters = [];
		var items = document.querySelectorAll("ul.main.version-chap.no-volumn.active li.wp-manga-chapter");
		for(var i=0; i<items.length; i++){
			var link = items[i].querySelector("a");
			if(!link) continue;
			var titleText = link.textContent.trim();
			var numStr = titleText.replace(/Chapter\s*/i, "");
			var num = parseFloat(numStr) || 0;
			var href = link.getAttribute("href");
			chapters.push({title: titleText, number: num, url: href});
		}
		return JSON.stringify(chapters);
	})();`

	// jsImages extracts the chapter image URLs.
	jsImages = `(function(){
		var imgs = document.querySelectorAll("div.reading-content img.wp-manga-chapter-img");
		var srcs = [];
		for(var i = 0; i < imgs.length; i++){
			var src = imgs[i].getAttribute("src") || imgs[i].getAttribute("data-src");
			if(src && src.trim() !== ""){
				srcs.push(src.trim());
			}
		}
		return JSON.stringify(srcs);
	})();`
)

// Global configuration variables loaded from environment variables.
var (
	remoteDebugURL string
	fastAPIBaseURL string
)

// initConfig loads environment variables and sets defaults if not provided.
func initConfig() {
	remoteDebugURL = os.Getenv("REMOTE_DEBUG_URL")
	if remoteDebugURL == "" {
		// Default if environment variable is not set.
		remoteDebugURL = "http://localhost:6082"
	}

	fastAPIBaseURL = os.Getenv("FASTAPI_BASE_URL")
	if fastAPIBaseURL == "" {
		// Default if environment variable is not set.
		fastAPIBaseURL = "http://localhost:6081"
	}
}

// triggerCloudflare calls the /trigger endpoint to bypass Cloudflare for the given URL.
func triggerCloudflare(seriesURL string) error {
	baseEndpoint := fmt.Sprintf("%s/trigger", fastAPIBaseURL)
	params := url.Values{}
	params.Add("url", seriesURL)
	params.Add("js", "")        // No extra JS is needed.
	params.Add("wait", "")      // No wait selector.
	params.Add("sleep", "5000") // 5000ms stabilization.
	fullURL := fmt.Sprintf("%s?%s", baseEndpoint, params.Encode())

	fmt.Printf("Calling /trigger endpoint to bypass Cloudflare: %s\n", fullURL)
	resp, err := http.Get(fullURL)
	if err != nil {
		return fmt.Errorf("HTTP GET request to /trigger failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("non-200 response from /trigger: %d, message: %s", resp.StatusCode, string(bodyBytes))
	}

	fmt.Println("Cloudflare bypass triggered. Waiting for the bypass to be completed...")
	return nil
}

// waitForBypass polls the series URL until the expected element is visible or until timeout.
func waitForBypass(seriesURL string, timeout time.Duration) error {
	start := time.Now()
	for {
		title, err := fetchExtraction(seriesURL, jsTitle, "div.post-title", 2000)
		if err == nil && strings.TrimSpace(title) != "" {
			fmt.Printf("Bypass completed; series title detected: %s\n", title)
			return nil
		}
		if time.Since(start) > timeout {
			return fmt.Errorf("timeout waiting for Cloudflare bypass completion")
		}
		fmt.Println("Waiting for Cloudflare bypass to complete...")
		time.Sleep(2 * time.Second)
	}
}

// fetchExtraction uses chromedp to navigate to targetURL, optionally waits for a CSS selector,
// sleeps for stabilization, and evaluates the provided JavaScript snippet.
func fetchExtraction(targetURL, jsSnippet, waitSelector string, sleepMs int) (string, error) {
	allocCtx, cancel := chromedp.NewRemoteAllocator(context.Background(), remoteDebugURL)
	defer cancel()

	ctx, cancel := chromedp.NewContext(allocCtx)
	defer cancel()

	ctx, cancel = context.WithTimeout(ctx, 60*time.Second)
	defer cancel()

	var res string
	actions := []chromedp.Action{
		chromedp.Navigate(targetURL),
	}
	if strings.TrimSpace(waitSelector) != "" {
		actions = append(actions, chromedp.WaitVisible(waitSelector, chromedp.ByQuery))
	}
	if sleepMs > 0 {
		actions = append(actions, chromedp.Sleep(time.Duration(sleepMs)*time.Millisecond))
	}
	actions = append(actions, chromedp.Evaluate(jsSnippet, &res))

	if err := chromedp.Run(ctx, actions...); err != nil {
		return "", err
	}
	return res, nil
}

// saveImageUsingFastAPI calls the FastAPI /save_image endpoint for the given chapter and image URL.
func saveImageUsingFastAPI(chapterURL, imageURL string) error {
	baseEndpoint := fmt.Sprintf("%s/save_image", fastAPIBaseURL)
	params := url.Values{}
	params.Add("chapter_url", chapterURL)
	params.Add("image_url", imageURL)
	fullURL := fmt.Sprintf("%s?%s", baseEndpoint, params.Encode())

	fmt.Printf("Calling /save_image endpoint: %s\n", fullURL)
	resp, err := http.Get(fullURL)
	if err != nil {
		return fmt.Errorf("HTTP GET request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("non-200 response from /save_image: %d, message: %s", resp.StatusCode, string(bodyBytes))
	}
	return nil
}

// getImageUsingFastAPI retrieves the JSON listing of saved images for the given chapter URL.
func getImageUsingFastAPI(chapterURL string) (string, error) {
	// Extract chapter folder from chapterURL.
	u, err := url.Parse(chapterURL)
	if err != nil {
		return "", fmt.Errorf("error parsing chapter URL: %w", err)
	}
	chapterFolder := path.Base(u.Path)
	if chapterFolder == "" {
		chapterFolder = "default_chapter"
	}

	baseEndpoint := fmt.Sprintf("%s/get_image", fastAPIBaseURL)
	params := url.Values{}
	params.Add("chapter", chapterFolder)
	fullURL := fmt.Sprintf("%s?%s", baseEndpoint, params.Encode())

	fmt.Printf("Calling /get_image endpoint for JSON list: %s\n", fullURL)
	resp, err := http.Get(fullURL)
	if err != nil {
		return "", fmt.Errorf("HTTP GET request to /get_image failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("non-200 response from /get_image: %d, message: %s", resp.StatusCode, string(bodyBytes))
	}
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("error reading /get_image response: %w", err)
	}
	return string(data), nil
}

// downloadImage retrieves an individual image file from the FastAPI /get_image endpoint
// and writes it to outputDir/<chapterFolder>/<filename>.
func downloadImage(chapterURL, filename, outputDir string) error {
	// Parse chapter folder from chapterURL.
	u, err := url.Parse(chapterURL)
	if err != nil {
		return fmt.Errorf("error parsing chapter URL: %w", err)
	}
	chapterFolder := path.Base(u.Path)
	if chapterFolder == "" {
		chapterFolder = "default_chapter"
	}

	baseEndpoint := fmt.Sprintf("%s/get_image", fastAPIBaseURL)
	params := url.Values{}
	params.Add("chapter", chapterFolder)
	params.Add("filename", filename)
	fullURL := fmt.Sprintf("%s?%s", baseEndpoint, params.Encode())

	fmt.Printf("Downloading image from: %s\n", fullURL)
	resp, err := http.Get(fullURL)
	if err != nil {
		return fmt.Errorf("HTTP GET request for image failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("non-200 response when downloading image %s: %d, message: %s", filename, resp.StatusCode, string(bodyBytes))
	}

	// Create the local chapter folder under outputDir.
	chapterOutputDir := path.Join(outputDir, chapterFolder)
	if err = os.MkdirAll(chapterOutputDir, 0755); err != nil {
		return fmt.Errorf("error creating chapter output directory: %w", err)
	}
	outputPath := path.Join(chapterOutputDir, filename)
	outFile, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("error creating file %s: %w", outputPath, err)
	}
	defer outFile.Close()

	// Write the response body (image file) to the file.
	if _, err = io.Copy(outFile, resp.Body); err != nil {
		return fmt.Errorf("error writing image %s: %w", outputPath, err)
	}
	fmt.Printf("Downloaded image %s to %s\n", filename, outputPath)
	return nil
}

// parseChapterRange parses a string range (e.g., "1-5") and returns the start and end values.
func parseChapterRange(rangeStr string) (float64, float64, error) {
	rangeParts := strings.Split(rangeStr, "-")
	if len(rangeParts) != 2 {
		return 0, 0, fmt.Errorf("invalid chapter range format. Use start-end")
	}
	startChap, err := strconv.ParseFloat(rangeParts[0], 64)
	if err != nil {
		return 0, 0, fmt.Errorf("invalid start chapter: %w", err)
	}
	endChap, err := strconv.ParseFloat(rangeParts[1], 64)
	if err != nil {
		return 0, 0, fmt.Errorf("invalid end chapter: %w", err)
	}
	return startChap, endChap, nil
}

// filterAndSortChapters filters the chapters within the given range and sorts them.
func filterAndSortChapters(chapters []ChapterInfo, startChap, endChap float64) []ChapterInfo {
	var selected []ChapterInfo
	for _, chap := range chapters {
		if chap.Number >= startChap && chap.Number <= endChap {
			selected = append(selected, chap)
		}
	}
	sort.Slice(selected, func(i, j int) bool {
		return selected[i].Number < selected[j].Number
	})
	return selected
}

func main() {
	// Initialize configuration.
	initConfig()

	// Setup CLI arguments and usage.
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s <series_url> <chapter_range> --output-dir <directory>\n", os.Args[0])
		flag.PrintDefaults()
	}
	outputDir := flag.String("output-dir", "./bin", "Output directory for bin")
	flag.Parse()

	args := flag.Args()
	if len(args) < 2 {
		flag.Usage()
		os.Exit(1)
	}
	seriesURL := args[0]
	chapterRange := args[1]

	fmt.Printf("Series URL: %s\n", seriesURL)
	fmt.Printf("Chapter Range: %s\n", chapterRange)
	fmt.Printf("Output Directory: %s\n", *outputDir)

	if err := os.MkdirAll(*outputDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "Error creating output directory: %v\n", err)
		os.Exit(1)
	}

	// Trigger the Cloudflare bypass.
	fmt.Println("Bypassing Cloudflare using /trigger endpoint...")
	if err := triggerCloudflare(seriesURL); err != nil {
		fmt.Fprintf(os.Stderr, "Error during Cloudflare bypass: %v\n", err)
		os.Exit(1)
	}

	// Wait until the series title is available (or timeout after 30 seconds).
	if err := waitForBypass(seriesURL, 30*time.Second); err != nil {
		fmt.Fprintf(os.Stderr, "Error waiting for Cloudflare bypass completion: %v\n", err)
		os.Exit(1)
	}

	// Extract series title.
	fmt.Println("Fetching series title...")
	title, err := fetchExtraction(seriesURL, jsTitle, "div.post-title", 5000)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error fetching title: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Series Title: %s\n", title)

	// Extract chapters list.
	fmt.Println("Fetching chapters list...")
	chaptersJSON, err := fetchExtraction(seriesURL, jsChapters, "ul.main.version-chap.no-volumn.active", 5000)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error fetching chapters list: %v\n", err)
		os.Exit(1)
	}
	var chapters []ChapterInfo
	if err := json.Unmarshal([]byte(chaptersJSON), &chapters); err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing chapters JSON: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Total chapters fetched: %d\n", len(chapters))

	// Parse chapter range.
	startChap, endChap, err := parseChapterRange(chapterRange)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing chapter range: %v\n", err)
		os.Exit(1)
	}

	selectedChapters := filterAndSortChapters(chapters, startChap, endChap)
	fmt.Printf("Chapters to download: %d\n", len(selectedChapters))
	if len(selectedChapters) == 0 {
		fmt.Println("No chapters found in the specified range.")
		os.Exit(0)
	}

	// Process each selected chapter.
	for _, chap := range selectedChapters {
		fmt.Printf("\nProcessing Chapter: %s (Chapter %.2f)\n", chap.Title, chap.Number)
		imagesJSON, err := fetchExtraction(chap.URL, jsImages, "div.reading-content", 5000)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error fetching images for chapter %.2f: %v\n", chap.Number, err)
			continue
		}
		var imageURLs []string
		if err := json.Unmarshal([]byte(imagesJSON), &imageURLs); err != nil {
			fmt.Fprintf(os.Stderr, "Error parsing images JSON for chapter %.2f: %v\n", chap.Number, err)
			continue
		}
		fmt.Printf("Found %d images in chapter %.2f\n", len(imageURLs), chap.Number)

		// Loop through all images and call the /save_image endpoint.
		for i, imgURL := range imageURLs {
			fmt.Printf("Saving image %d via /save_image endpoint: %s\n", i+1, imgURL)
			if err := saveImageUsingFastAPI(chap.URL, imgURL); err != nil {
				fmt.Fprintf(os.Stderr, "Error saving image %d in chapter %.2f: %v\n", i+1, chap.Number, err)
			} else {
				fmt.Printf("Saved image %d for chapter %.2f via /save_image endpoint\n", i+1, chap.Number)
			}
			time.Sleep(500 * time.Millisecond) // Brief pause between requests.
		}

		// Retrieve the list of saved images.
		response, err := getImageUsingFastAPI(chap.URL)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error retrieving saved image info for chapter %.2f: %v\n", chap.Number, err)
			continue
		}

		// Parse the JSON response.
		var chapterImgs ChapterImages
		if err := json.Unmarshal([]byte(response), &chapterImgs); err != nil {
			fmt.Fprintf(os.Stderr, "Error parsing saved image info JSON for chapter %.2f: %v\n", chap.Number, err)
			continue
		}

		fmt.Printf("Downloading %d saved images for chapter %.2f\n", len(chapterImgs.Images), chap.Number)
		for _, filename := range chapterImgs.Images {
			if err := downloadImage(chap.URL, filename, *outputDir); err != nil {
				fmt.Fprintf(os.Stderr, "Error downloading image %s for chapter %.2f: %v\n", filename, chap.Number, err)
			}
		}
	}

	fmt.Println("\nDownload complete.")
}
