#!/usr/bin/env python

# Internal
import os
import sys
import subprocess
import traceback

# 3rdparty
import requests

try:
  import parted
except:
  traceback.print_exc()
  subprocess.run([
    sys.executable, *('-m pip install --user pyparted'.split())
  ])
  import parted

def resume_download(fileurl, resume_byte_pos):
    resume_header = {'Range': 'bytes=%d-' % resume_byte_pos}
    return requests.get(fileurl, headers=resume_header, stream=True,  verify=False, allow_redirects=True)

def read_block_device_size(block_file):
  with open(block_file, 'rb') as f:
    return f.seek(0, 2) or f.tell()


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

  block_devices_to_burn = [
    '/dev/mmcblk0', # TODO add more?
  ]
  block_device_to_burn = None
  for b in block_devices_to_burn:
    if os.path.exists(b):
      block_device_to_burn = b
      break

  if block_device_to_burn is None:
    print(f'Cannot find any block devices to burn! (Searched {block_devices_to_burn})')
  else:
    block_dev_size_gb = round(read_block_device_size(block_device_to_burn) / 1000000000.0, 1)
    yn = input(f'About to burn to {block_device_to_burn} ({block_dev_size_gb}gb), confirm? (y/n)')
    if not 'y' in yn.lower():
      print('Aborting!')
      sys.exit(0)

  subprocess.run([
    'sh', '-c', f'sudo umount {block_device_to_burn}*'
  ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, check=False)
  subprocess.run([
    'sh', '-c', f'sync'
  ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, check=False)

  print(f'Burning {block_device_to_burn} ...')

  os.makedirs('build/mount_boot', exist_ok=True)
  os.makedirs('build/mount_root', exist_ok=True)
  
  device = parted.getDevice(block_device_to_burn)
  disk = parted.freshDisk(device, 'msdos')

  # For some reason 2048 == 1mb of space using the parted.Geometry class; is this related to block sizes?
  boot_partition_size = 512 * 2048 # 512-mb boot

  boot_geometry = parted.Geometry(device=device, start=1, length=boot_partition_size)
  
  boot_filesystem = parted.FileSystem(type='fat32', geometry=boot_geometry)
  
  boot_partition = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL,
                               fs=boot_filesystem, geometry=boot_geometry)
  
  disk.addPartition(partition=boot_partition, constraint=device.optimalAlignedConstraint)
  boot_partition.setFlag(parted.PARTITION_BOOT)


  root_geometry = parted.Geometry(device=device, start=1 + boot_partition_size + 1, length=device.getLength() - (1 + boot_partition_size + 1) )
  
  root_filesystem = parted.FileSystem(type='ext4', geometry=root_geometry)
  
  root_partition = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL,
                               fs=root_filesystem, geometry=root_geometry)
  
  disk.addPartition(partition=root_partition, constraint=device.optimalAlignedConstraint)
  
  try:
    disk.commit()
  except:
    if not 'unable to inform the kernel of the change' in traceback.format_exc():
      traceback.print_exc()

  subprocess.run(['sync'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, check=False)
  subprocess.run(['sudo', 'partprobe', str(block_device_to_burn)], check=False)

  print(f'Done writing to {block_device_to_burn}!')

  subprocess.run(['lsblk', str(block_device_to_burn)], check=False)






if __name__ == '__main__':
  main()
