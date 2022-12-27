"""
Simple script to organize photos into folders
"""
import os
import argparse
import shutil
import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from pillow_heif import register_heif_opener
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

register_heif_opener()

extensions_img = [
    '.jpg',
    '.jpeg',
    '.heic',
    '.dng',
    '.cr2',
    '.png'
]

extensions_vid = [
    '.mov',
    '.avi',
    '.mp4',
    '.3gp',
    '.3gpp',
    '.mpg'
]


def do(folder, output_folder=None, recursive=False, test_mode=False, debug=False):
    print('source_folder: {}'.format(folder))
    print('output_folder: {}'.format(output_folder))
    print('recursive: {}'.format(recursive))
    print('test_mode: {}'.format(test_mode))
    print('debug_mode: {}'.format(debug))

    if debug:
        print('img extensions: {}'.format(extensions_img))
        print('vid extensions: {}'.format(extensions_vid))

    if os.path.isdir(folder):
        print('looking for files')
        images = []
        movies = []
        others = []

        for file in ls(folder, recursive):
            ext = os.path.splitext(file)[-1].lower()

            if not os.path.isdir(file):
                if ext in extensions_img:
                    images.append(file)
                elif ext in extensions_vid:
                    movies.append(file)
                else:
                    others.append(file)

        print('found {} image(s)'.format(len(images)))
        print('found {} movie(s)'.format(len(movies)))
        print('found {} other(s)'.format(len(others)))

        for file in images + movies:
            print('file {}'.format(file))
            file_name_only = os.path.basename(file)
            file_folder = os.path.dirname(os.path.abspath(file))

            # Try Exif data
            try:
                if file in images:
                    im = Image.open(file)

                    exif = {
                        TAGS[k]: v
                        for k, v in im._getexif().items()
                        if k in TAGS
                    }

                    # choose the date/time in the order of preference
                    if exif.get('DateTimeOriginal'):
                        date_to_use = exif.get('DateTimeOriginal')
                    elif exif.get('DateTimeDigitized'):
                        date_to_use = exif.get('DateTimeDigitized')
                    else:
                        date_to_use = exif.get('DateTime')

                    date_exif = datetime.datetime.strptime(date_to_use, '%Y:%m:%d %H:%M:%S')

                    if debug:
                        print('file is a video')
                        print('datetime: {}'.format(date_exif))

                    im.close()
                else:
                    parser = createParser(file)
                    metadata = extractMetadata(parser).exportDictionary()['Metadata']

                    date_to_use = metadata['Creation date']
                    date_exif = datetime.datetime.strptime(date_to_use, '%Y-%m-%d %H:%M:%S')

                    if debug:
                        print('file is a video')
                        print('datetime: {}'.format(date_exif))

            except Exception as e:
                # Try to extract date from the file name
                # iPhone usually YYYY-MM-DD_HH-MI-SS_SSS
                # Android ZTE usually IMG_YYYYMMDD_HHMISS
                # Android Samsung usually YYYYMMDD_HHMISS

                # Get first 10 characters of the file name
                identifiers = [
                    file_name_only[0:10].replace('-', ''),
                    file_name_only[4:12],
                    file_name_only[0:8]
                ]

                date_filename = ''

                for identifier in identifiers:
                    try:
                        date_filename = datetime.datetime.strptime(
                            identifier,'%Y%m%d')
                    except Exception as e:
                        pass
                    else:
                        break

                # Get file creation time if no success
                if not date_filename:
                    print('date found from ctime')
                    date_media = datetime.datetime.fromtimestamp(os.path.getctime(file))
                else:
                    print('date found from file name')
                    date_media = date_filename

            else:
                print('date found from exif')
                date_media = date_exif

            date_media = date_media.strftime('%Y/%m/%d')

            if output_folder is None:
                target_folder = os.path.join(file_folder, date_media)
            else:
                target_folder = os.path.join(output_folder, date_media)
            target_file = os.path.join(target_folder, file_name_only)
            print('file will move to %s' % target_file)

            # move file
            # check if target folder exists
            if not os.path.isdir(target_folder) and not test_mode:
                os.makedirs(target_folder, exist_ok=True)

            if not test_mode:
                if not shutil.move(file, target_file):
                    print('could not move the file %s' % file)
                else:
                    print('moved OK')

    else:
        print('you specified an invalid folder')


def ls(path, recursive=False):
    files = [os.path.join(path, file) for file in os.listdir(path)]
    if recursive:
        for file in files:
            if os.path.isdir(file):
                files = files + ls(file, recursive)

    return files


if __name__ == '__main__':
    # Set command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', help='full path of the folder containing photos')
    parser.add_argument('--output_folder', help='full path of the output folder')
    parser.add_argument('--recursive', action='store_true',help='scan folder recursively')
    parser.add_argument('--test_mode', action='store_true', help='no changes to be made')
    parser.add_argument('--debug', action='store_true', help='debug mode')
    args = parser.parse_args()

    do(folder=args.folder, output_folder=args.output_folder, recursive=args.recursive, test_mode=args.test_mode,
       debug=args.debug)