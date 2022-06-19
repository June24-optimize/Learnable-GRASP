import numpy as np
from helpers.post_process import interpolate_slice
from datetime import datetime
import os
import nibabel as nib
import argparse
from parameters.param_parse import PostProcessParamParse
import scipy.io as sio

parser = argparse.ArgumentParser(description='Arguments for Post Processing')
parser.add_argument('-p', '--root_json',
                    required=True,
                    type=str,
                    default='./parameters/p_proc_params.json',
                    help='[parameters] Path to grasp_params.json file')
parser.add_argument('-d', '--root_rec',
                    required=True,
                    type=str,
                    default=None,
                    help='[domain] Path that that includes raw_rec')

parser.add_argument('-o', '--root_out',
                    required=True,
                    type=str,
                    default=None,
                    help='[output] Save path')

args = parser.parse_args()

param_parser = PostProcessParamParse(json_path=args.root_json)
parameters = param_parser.get_param_val()

# General parameters
root_rec = args.root_rec
rec_save_folder = args.root_out
# Post Processing Parameters
post_img_size = parameters['post_img_size']
rate_os = parameters['rate_os']
flag_fft_shift = parameters['flag_fft_shift']
dx = parameters['dx']
dy = parameters['dy']
dz = parameters['dz']

folder_raw_rec = root_rec
# folder_raw_rec = os.path.join(root_rec, 'raw-rec')
# assert os.path.exists(folder_raw_rec), "No raw files detected at:{}".format(
#     folder_raw_rec)

rec_volume = []
for rec_file in os.listdir(folder_raw_rec):
    rec_volume.append(sio.loadmat(os.path.join(folder_raw_rec, rec_file))['rec'])
rec_volume = np.array(rec_volume)

init_num_slice = rec_volume.shape[0]
# Interpolate slices to match previous reconstructions
rec_volume = interpolate_slice(rec_volume, post_img_size, rate_os, flag_fft_shift)

now = datetime.now()
date_time = now.strftime("%m_%d_%Y_%H_%M_%S")

print("Saving...")
# To save in nifti format the data should be uint16
max_p = np.max(np.abs(rec_volume))
min_p = np.min(np.abs(rec_volume))
rec_vol_16 = np.array(np.round((np.abs(rec_volume) - min_p) /
                               (max_p - min_p) * 2 ** 15), dtype=np.uint16)
# save 4D volume
# Change dimensions from NSl x Nv x Ns x Ns to Ns x Ns x NSl x Nv
rec_vol_16 = np.transpose(rec_vol_16, [2, 3, 0, 1])
file_name = os.path.join(rec_save_folder, date_time + '-rec4D.nii.gz')
nii_dat = nib.Nifti1Image(rec_vol_16, np.eye(4))

nii_dat.header['pixdim'][1] = dx #1.33929
nii_dat.header['pixdim'][2] = dy #1.33929
nii_dat.header['pixdim'][3] = dz #3.50018 * init_num_slice / post_img_size[0]

if not os.path.exists(rec_save_folder):
    os.makedirs(rec_save_folder)

nii_dat.to_filename(file_name)
param_file = os.path.join(rec_save_folder, date_time + '-params.json')
param_parser.save_struct_to_file(param_file)
