#!/usr/bin/env python

# Internal
import os
import sys
import subprocess

# 3rdparty
import requests

def resume_download(fileurl, resume_byte_pos):
    resume_header = {'Range': 'bytes=%d-' % resume_byte_pos}
    return requests.get(fileurl, headers=resume_header, stream=True,  verify=False, allow_redirects=True)

def main(args=sys.argv):
  os.makedirs('build', exist_ok=True)

  image_url = 'http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-aarch64-latest.tar.gz'
  image_tarball_file = os.path.join('build', os.path.basename(image_url))
  if not os.path.exists(image_tarball_file):
    with open(image_tarball_file, 'wb') as fd:
      fd.write(b'')

  print(f'Downloading {image_url} to {image_tarball_file}')
  subprocess.run([
    #'curl', '-L', '-O', '-C', '-', '-o', image_tarball_file, image_url
    'wget', '-c', '-O', image_tarball_file, image_url
  ])
  print(f'{image_tarball_file} downloaded!')






if __name__ == '__main__':
  main()
