#!/usr/bin/env python

# Copyright (c) 2012, Ozan Sener
# Contributor (c) 2016, Paulo Miguel Almeida Rodenas
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#   * Neither the name of copyright holders nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

try:
    from urllib.parse import urlparse, urlencode, parse_qsl
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError
    from http.client import HTTPException
except ImportError:
    from urlparse import urlparse, parse_qsl
    from urllib import urlencode
    from urllib2 import urlopen, HTTPError, URLError
    from httplib import HTTPException

from os.path import basename, splitext, isfile
import codecs
import argparse
import sys
import xml.etree.ElementTree as ET
from collections import namedtuple

TRACK_URL = 'http://video.google.com/timedtext?%s'
LIST_URL = 'http://www.youtube.com/api/timedtext?%s'
TRACK_KEYS = 'id name lang_original lang_translated lang_default'

Track = namedtuple('Track', TRACK_KEYS)
Line = namedtuple('Line', 'start duration text')


def save_srt(caption, filename):
    """Save a list of srt formatted lines in a srt file with UTF-8 BOM"""
    with codecs.open(filename, 'w', 'utf-8-sig') as srt_file:
        srt_file.writelines(caption)


def retrieve_caption(video_id, languages):
    """
    Fetch the first available track in a language list, convert it to srt and
    return the list of lines for a given youtube video_id.
    """
    track = get_track(video_id, languages)
    caption = convert_caption(track)

    return caption


def get_track(video_id, languages):
    """Return the first available track in a language list for a video."""
    tracks = get_track_list(video_id)
    for lang in languages:
        if lang in tracks:
            break
    else:
        return

    track = tracks[lang]
    url = TRACK_URL % urlencode({'name': track.name, 'lang': lang,
                                        'v': video_id})
    track = urlopen(url)

    return parse_track(track)


def get_track_list(video_id):
    """Return the list of available captions for a given youtube video_id."""
    url = LIST_URL % urlencode({'type': 'list', 'v': video_id})
    captions = {}
    try:
        data = urlopen(url)
        tree = ET.parse(data)
        for element in tree.iter('track'):
            lang = element.get('lang_code')
            fields = map(element.get, TRACK_KEYS.split())
            captions[lang] = Track(*fields)
    except (URLError, HTTPError, HTTPException) as err:
        print("Network error: Unable to retrieve %s\n%s" % (url, err))
        sys.exit(6)
    return captions


def parse_track(track):
    """Parse a track returned by youtube and return a list of lines."""
    lines = []

    tree = ET.parse(track)
    for element in tree.iter('text'):
        if not element.text:
            continue
        start = float(element.get('start'))
        # duration is sometimes unspecified
        duration = float(element.get('dur') or 0)
        text = element.text
        lines.append(Line(start, duration, text))

    return lines


def convert_caption(caption):
    """Convert each line in a caption to srt format and return a list."""
    if not caption:
        return
    lines = []
    for num, line in enumerate(caption, 1):
        start, duration = line.start, line.duration
        if duration:
            end = start + duration  # duration of the line is specified
        else:
            if caption[num]:
                end = caption[num].start  # we use the next start if available
            else:
                end = start + 5  # last resort
        line = u'%(num)i\r\n%(start)s --> %(end)s\r\n%(text)s\r\n\r\n' % \
               {'num': num,
                'start': convert_time(start),
                'end': convert_time(end),
                'text': line.text}
        line = line.replace('&quot;', '"')\
                   .replace('&amp;', '&')\
                   .replace('&#39;', '\'')
        lines.append(line)

    return lines


def convert_time(time):
    """Convert given time to srt format."""
    stime = '%(hours)02d:%(minutes)02d:%(seconds)02d,%(milliseconds)03d' % \
            {'hours': time / 3600,
             'minutes': (time % 3600) / 60,
             'seconds': time % 60,
             'milliseconds': (time % 1) * 1000}
    return stime


def main():
    parser = argparse.ArgumentParser(description="Download closed captions of \
                                     a YouTube video as a SRT file.")
    parser.add_argument('uri',
                        metavar='VIDEO_URL_OR_FILENAME',
                        help="YouTube video url or filename")
    parser.add_argument('-l', '--lang',
                        metavar='l1 [,l2...]', default='en',
                        help="comma separated list of two letter language \
                        codes (default: en)")
    parser.add_argument('-o', '--output',
                        help="write captions to FILE instead of video_id.srt")
    args = parser.parse_args()

    if args.uri.startswith('http'):
        queries = dict(parse_qsl(urlparse(args.uri).query))

        video_id = queries.get('v')
        output = args.output or video_id
        output = output if output.endswith('.srt') else output + '.srt'
        lang = args.lang.split(',')

        caption = retrieve_caption(video_id, lang)

        if caption:
            save_srt(caption, output)
            return

        captions = get_track_list(video_id)
        if captions:
            print("Available languages:")
            for lang in captions:
                print("  %(code)s\t%(original)s (%(translated)s)" % \
                    {'code': lang,
                     'original': captions[lang].lang_original,
                     'translated': captions[lang].lang_translated})
        else:
            print("There are no subtitles available for this video: %s" % args.uri)
    else:
        if isfile(args.uri):
            output = args.output or splitext(basename(args.uri))[0]
            output = output if output.endswith('.srt') else output + '.srt'

            track = parse_track(args.uri)
            caption = convert_caption(track)

            if caption:
                save_srt(caption, output)
                return
        else:
            print("There is no such file: %s" % args.uri)

if __name__ == '__main__':
    main()
