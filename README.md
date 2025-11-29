# Medium Article Downloader

A Python tool to download Medium articles as Markdown files with all images included. This tool handles Medium's anti-scraping measures using multiple fallback methods to ensure reliable article downloads.

**Repository**: [https://github.com/mahmoud0x01/medium-to-markdown](https://github.com/mahmoud0x01/medium-to-markdown)

## Features

- 📄 **Download Medium articles** as clean Markdown files
- 🖼️ **Download all images** from articles to a local `_media/` directory
- 🔄 **Multiple fallback methods** to bypass Medium's anti-scraping measures
- 🔗 **Automatic image reference updates** - all image links in markdown point to local files
- 📝 **Auto-generated filenames** based on article titles
- 🛡️ **Robust error handling** with helpful error messages

## Installation

### Prerequisites

- Python 3.7 or higher
- `curl` (for image download fallback - usually pre-installed on Linux/macOS)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/mahmoud0x01/medium-to-markdown.git
cd medium-to-markdown
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python3 download_medium.py <medium_url> [output_file]
```

### Examples

```bash
# Download with auto-generated filename
python3 download_medium.py https://medium.com/@user/article-title

# Download with custom output filename
python3 download_medium.py https://medium.com/@user/article-title my-article.md
```

### Real Example

```bash
python3 download_medium.py 'https://medium.com/@mahmoudadel0x/computer-security-binary-hacking-concepts-and-basics-fae791a80c49'
```

This will:
1. Fetch the article content
2. Download all images to `_media/` directory
3. Create a markdown file with the article title
4. Update all image references to point to local files

## How It Works

The tool uses multiple strategies to handle Medium's anti-scraping measures:

1. **Direct Access**: Attempts to fetch the article with browser-like headers
2. **RSS Feed Fallback**: If direct access fails, tries to fetch via Medium's RSS feed
3. **Curl Fallback**: For images that fail with Python requests, uses `curl` as a fallback
4. **Smart Image Handling**: Automatically downloads and renames images, updating all references

## Project Structure

```
.
├── download_medium.py    # Main script
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── .gitignore           # Git ignore rules
└── _media/              # Downloaded images (created automatically)
```

## Dependencies

- `requests` - HTTP library for fetching articles
- `beautifulsoup4` - HTML parsing
- `html2text` - HTML to Markdown conversion
- `lxml` - Fast XML/HTML parser

## Troubleshooting

### 403 Forbidden Errors

If you encounter 403 errors, the tool will automatically try alternative methods. If all methods fail:

1. **Check if the article is public** - Some Medium articles require authentication
2. **Try using a VPN** - Your IP might be temporarily blocked
3. **Wait a few minutes** - Rate limiting may be in effect
4. **Use browser extensions** - As an alternative, try browser extensions like "MarkDownload" or "SingleFile"

### Image Download Failures

If some images fail to download:
- The tool will continue and markdown will still be created
- Failed images will show error messages
- You can manually download images and place them in `_media/` directory

### Missing curl

If `curl` is not installed:
- On Ubuntu/Debian: `sudo apt-get install curl`
- On macOS: Usually pre-installed
- On Windows: Install via [curl for Windows](https://curl.se/windows/) or use Git Bash

## Limitations

- **Private/Paid Articles**: Cannot download articles behind Medium's paywall
- **Rate Limiting**: Too many requests may trigger temporary blocks
- **JavaScript Content**: Some dynamically loaded content may not be captured
- **Image CDN Restrictions**: Some images may fail if Medium's CDN blocks the request

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and personal use only. Please respect Medium's Terms of Service and robots.txt. Use responsibly and don't abuse the service.

## Author

Created with ❤️ for the open-source community.

## Acknowledgments

- Thanks to the Medium community for great content
- Built with Python and open-source libraries

