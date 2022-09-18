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
register_heif_opener()

extensions_img = [
    '.jpg',
    '.jpeg',
    '.heic'
]

extensions_vid = [
    '.mov',
    '.avi',
    '.mp4'
]


def do(folder, recursive=False, test_mode=False):
    print('using folder: %s' % folder)
    print('recursive: %s' % recursive)
    print('test_mode: %s' % test_mode)

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

        print('found %s image(s)' % len(images))
        print('found %s movie(s)' % len(movies))
        print('found %s other(s)' % len(others))

        for file in images + movies:
            print('file %s' % file)
            file_name_only = os.path.basename(file)
            file_folder = os.path.dirname(os.path.abspath(file))

            # Try Exif data
            try:
                im = Image.open(file)

                exif = {
                    TAGS[k]: v
                    for k, v in im.getexif().items()
                    if k in TAGS
                }
                print(exif)

                date_exif = datetime.datetime.strptime(exif['DateTime'],
                                                       '%Y:%m:%d %H:%M:%S')
                im.close()
            except Exception as e:
                if im:
                    im.close()

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
                    date_media = datetime.datetime.fromtimestamp(os.path.getctime(
                    file))
                else:
                    print('date found from file name')
                    date_media = date_filename

            else:
                print('date found from exif')
                date_media = date_exif

            date_media = date_media.strftime('%Y/%m/%d')
            target_folder = os.path.join(file_folder, date_media)
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
    parser.add_argument('folder', help='full path of the folder containing '
                                       'photos')
    parser.add_argument('--recursive', action='store_true',help='scan folder '
                                                                'recursively')

    parser.add_argument('--test_mode', action='store_true', help='no changes '
                                                                 'to be made')
    args = parser.parse_args()

    do(folder=args.folder, recursive=args.recursive, test_mode=args.test_mode)