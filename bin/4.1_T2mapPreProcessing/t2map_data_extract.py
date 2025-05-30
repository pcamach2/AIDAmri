import nibabel as nii
import numpy as np
import argparse
import os
import glob
import csv
import sys  # Added import statement for sys module

def getOutfile(atlas_type, img_file, suffix):
    imgName = os.path.basename(img_file)
    t2map = str.split(imgName, '.')[-3]
    acronym_name = os.path.basename(atlas_type).split('.')[0]
    outFile = os.path.join(os.path.dirname(img_file), f"{t2map}_T2values_{acronym_name}_{suffix}.csv")
    return outFile

def extractT2MapdataMean(img, rois, outfile, txt_file):
    slices = np.unique(np.where(rois > 0)[2])
    regions = np.delete(np.unique(rois), 0)
    
    indices = None
    if txt_file is not None:
        ref_lines = open(txt_file).readlines()
        indices = {int(line.split('\t')[0]): line.split('\t')[1].strip() for line in ref_lines}
    
    with open(outfile, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Slice", "ARA IDs", "Names", "T2 Values", "Region Sizes"])
        
        for s in slices:
            for r in regions:
                region_voxels = np.where((rois[:, :, s] == r) & (rois[:, :, s] > 0))
                if len(region_voxels[0]) == 0:
                    continue
                mean_value = np.mean(img[region_voxels])
                region_size = len(region_voxels[0])
                acro = indices.get(r, "")  # Using dict.get() to avoid KeyError
                csv_writer.writerow([s, r, acro, "%.2f" % mean_value, "%.2f" % region_size])

def extractT2MapdataPerRegion(img, rois, outfile, txt_file):
    regions = np.delete(np.unique(rois), 0)
    
    indices = None
    if txt_file is not None:
        ref_lines = open(txt_file).readlines()
        indices = {int(line.split('\t')[0]): line.split('\t')[1].strip() for line in ref_lines}
    
    with open(outfile, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["ARA IDs", "Names", "T2 Values", "Region Sizes"])
        
        for r in regions:
            region_voxels = np.where((rois == r) & (rois > 0))
            if len(region_voxels[0]) == 0:
                continue
            mean_value = np.mean(img[region_voxels])
            region_size = len(region_voxels[0])
            acro = indices.get(r, "")  # Using dict.get() to avoid KeyError
            csv_writer.writerow([r, acro, "%.2f" % mean_value, "%.2f" % region_size])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extracts the T2 values from the T2 map for every atlas region')
    requiredNamed = parser.add_argument_group('Required named arguments')
    requiredNamed.add_argument('-i', '--input', help='Input T2 map, should be a nifti file')
    args = parser.parse_args()

    acronyms_files = glob.glob(os.path.join(os.getcwd(), "*.txt"))
    print(f"Extracting T2 values for: {args.input}")
    print(f"Acronym files: {acronyms_files}")

    # Checking if input file is provided
    if args.input is None:
        sys.exit("Error: No input file provided.")

    image_file = args.input
    if not os.path.exists(image_file):
        sys.exit(f"Error: '{image_file}' is not an existing image nii-file.")

    img_data = nii.load(image_file)
    img = img_data.get_fdata()  # Using get_fdata() for compatibility
    
    parental_atlas = glob.glob(os.path.join(os.path.dirname(image_file), "*AnnoSplit_parental.nii*"))[0]
    non_parental_atlas = glob.glob(os.path.join(os.path.dirname(image_file), "*AnnoSplit.nii*"))[0]

    for acronyms in acronyms_files:  # Corrected variable name to acronyms
        try:
            if "parentARA_LR" in acronyms:
                atlas_type = "parental"
                atlas = parental_atlas
            else:
                atlas_type = "non-parental"
                atlas = non_parental_atlas

            roi_data = nii.load(atlas)
            rois = roi_data.get_fdata()  # Using get_fdata() for compatibility

            outFileMean = getOutfile(atlas_type, image_file, "Mean")  # Fixed suffix to "Mean"
            print(f"Outfile (Mean): {outFileMean}")
            extractT2MapdataMean(img, rois, outFileMean, acronyms)

            outFilePerRegion = getOutfile(atlas_type, image_file, "PerRegion")  # Fixed suffix to "PerRegion"
            print(f"Outfile (Per Region): {outFilePerRegion}")
            extractT2MapdataPerRegion(img, rois, outFilePerRegion, acronyms)
        except Exception as e:
            print(f'Error while processing the T2 values: {str(e)}')  # Improved error message
            raise  # Raising the exception to halt execution

    print("Finished T2 map processing")
