youtube2srt
===========

A small command-line utility I had laying around for a good while that allows you to download closed captions from YouTube as a SRT file.

```
usage: youtube2srt.py [-h] [-l l1 [,l2...]] [-o OUTPUT] VIDEO_URL_OR_FILENAME

Download closed captions of a YouTube video as a SRT file.

positional arguments:
  VIDEO_URL_OR_FILENAME
                        YouTube video url or filename

optional arguments:
  -h, --help            show this help message and exit
  -l l1 [,l2...], --lang l1 [,l2...]
                        comma separated list of two letter language codes
                        (default: en)
  -o OUTPUT, --output OUTPUT
                        write captions to FILE instead of video_id.srt
```
