#!/usr/bin/env python

def read_yml_file(yml_filepath):
    import yaml
    with open(yml_filepath,"r") as f:
        yml_dict = yaml.load(f)

    return yml_dict


def write_yml_file(yml_dict, out_filepath):
    import yaml
    with open(out_filepath, "wt") as f:
        yaml.dump(yml_dict, f)


def read_txt_file(txt_file):
    with open(txt_file,"r") as f:
        strings = f.read().splitlines()
    return strings


def write_txt_file(text_lines, out_filepath):
    with open(out_filepath, "wt") as f:
        for line in text_lines:
            print >>f, line, "\n"


def read_pickle(pickle_file):
    import pickle
    with open(pickle_file, "r") as f:
        dct = pickle.load(f)
    return dct


def write_pickle(dct, out_filepath):
    import pickle
    with open(out_filepath, "wt") as f:
        pickle.dump(dct, f, protocol=pickle.HIGHEST_PROTOCOL)


def gather_filepaths(output_folder_path):
    import os
    filepaths = []

    for root, dirs, files in os.walk(output_folder_path):
        # loops through every file in the directory
        for filename in files:
            # checks if the file is a nifti (.nii.gz)
            if '.nii' in filename or '.csv' in filename or '.txt' in filename or '.1D' in filename:
                filepaths.append(os.path.join(root, filename))

    if len(filepaths) == 0:
        err = "\n\n[!] No filepaths were found given the output folder!\n\n"
        raise Exception(err)

    return filepaths


def pull_NIFTI_file_list_from_s3(s3_directory, s3_creds):

    import os
    try:
        from indi_aws import fetch_creds
    except:
        err = "\n\n[!] You need the INDI AWS package installed in order to " \
              "pull from an S3 bucket. Try 'pip install indi_aws'\n\n"
        raise Exception(err)

    s3_list = []

    s3_path = s3_directory.replace("s3://","")
    bucket_name = s3_path.split("/")[0]
    bucket_prefix = s3_path.split(bucket_name + "/")[1]

    bucket = fetch_creds.return_bucket(s3_creds, bucket_name)

    # Build S3-subjects to download
    # maintain the "s3://<bucket_name>" prefix!!
    for bk in bucket.objects.filter(Prefix=bucket_prefix):
        if ".nii" in str(bk.key):
            s3_list.append(os.path.join("s3://", bucket_name, str(bk.key)))

    if len(s3_list) == 0:
        err = "\n\n[!] No filepaths were found given the S3 path provided!" \
              "\n\n"
        raise Exception(err)

    return s3_list


def download_from_s3(s3_path, local_path, s3_creds):

    import os

    try:
        from indi_aws import fetch_creds, aws_utils
    except:
        err = "\n\n[!] You need the INDI AWS package installed in order to " \
              "pull from an S3 bucket. Try 'pip install indi_aws'\n\n"
        raise Exception(err)

    s3_path = s3_path.replace("s3://","")
    bucket_name = s3_path.split("/")[0]
    bucket_prefix = s3_path.split(bucket_name + "/")[1]

    filename = s3_path.split("/")[-1]
    local_file = os.path.join(local_path, filename)

    if not os.path.exists(local_file):
        bucket = fetch_creds.return_bucket(s3_creds, bucket_name)
        aws_utils.s3_download(bucket, ([bucket_prefix], [local_file]))

    return local_file


def concordance(x, y, rho):
    """
    Calculates Lin's concordance correlation coefficient.

    Usage: concordence(x, y) where x, y are equal-length arrays
    Returns: concordance correlation coefficient

    Note: strict than pearson
    """

    import math
    import numpy as np

    map(float, x)
    map(float, y)
    xvar = np.var(x)
    yvar = np.var(y)
    #rho = scipy.stats.pearsonr(x, y)[0]
    #p = np.corrcoef(x,y)  # numpy version of pearson correlation coefficient
    ccc = 2. * rho * math.sqrt(xvar) * math.sqrt(yvar) / (xvar + yvar + (np.mean(x) - np.mean(y))**2)

    return ccc


def test_create_unique_file_dict():

    from cpac_correlations_wf import create_unique_file_dict

    filepaths = [
      "/path/sub001/centrality_outputs/_scan_rest_1/degree_centrality_weighted.nii.gz",
      "/path/sub001/centrality_outputs/_scan_rest_1/eigenvector_centrality_weighted.nii.gz",
      "/path/sub002/alff_to_standard_smooth/_scan_rest_1/file.nii.gz"
    ]

    output_folder = "/path"

    # output dictionary should have dictionaries as values, which have tuples 
    # as keys, where the tuple identifies the same file across different CPAC
    # versions (and thus potentially different filepaths)
    #   multiple dictionary levels to make it easy to pull up all of the
    #   entries for one particular derivative
    ref_output = {
      'alff_to_standard_smooth':
        {('alff_to_standard_smooth', 
          '/sub002/alff_to_standard_smooth/_scan_rest_1/', '1'):
            ['/path/sub002/alff_to_standard_smooth/_scan_rest_1/file.nii.gz']},
      'centrality_outputs: degree': 
        {('centrality_outputs: degree', 
          '/sub001/centrality_outputs/_scan_rest_1/', '1'): 
            ['/path/sub001/centrality_outputs/_scan_rest_1/degree_centrality_weighted.nii.gz']},
      'centrality_outputs: eigenvector': 
        {('centrality_outputs: eigenvector', 
          '/sub001/centrality_outputs/_scan_rest_1/', '1'):
            ['/path/sub001/centrality_outputs/_scan_rest_1/eigenvector_centrality_weighted.nii.gz']}
    }

    file_dict = create_unique_file_dict(filepaths, output_folder)

    assert ref_output == file_dict


def test_create_unique_file_dict_with_replacements():

    from cpac_correlations_wf import create_unique_file_dict

    filepaths = [
      "/path/sub001_site1/centrality_outputs/_scan_rest_1/degree_centrality_weighted.nii.gz",
      "/path/sub001_site1/centrality_outputs/_scan_rest_1/eigenvector_centrality_weighted.nii.gz",
      "/path/sub002_site1/alff_to_standard_smooth/_scan_rest_1/file.nii.gz"
    ]

    output_folder = "/path"

    # remove _site1 and replace with nothing
    replacements = ["_site1,"]

    # output dictionary should have dictionaries as values, which have tuples 
    # as keys, where the tuple identifies the same file across different CPAC
    # versions (and thus potentially different filepaths)
    #   multiple dictionary levels to make it easy to pull up all of the
    #   entries for one particular derivative
    ref_output = {
      'alff_to_standard_smooth':
        {('alff_to_standard_smooth', 
          '/sub002/alff_to_standard_smooth/_scan_rest_1/', '1'):
            ['/path/sub002/alff_to_standard_smooth/_scan_rest_1/file.nii.gz']},
      'centrality_outputs: degree': 
        {('centrality_outputs: degree', 
          '/sub001/centrality_outputs/_scan_rest_1/', '1'): 
            ['/path/sub001/centrality_outputs/_scan_rest_1/degree_centrality_weighted.nii.gz']},
      'centrality_outputs: eigenvector': 
        {('centrality_outputs: eigenvector', 
          '/sub001/centrality_outputs/_scan_rest_1/', '1'):
            ['/path/sub001/centrality_outputs/_scan_rest_1/eigenvector_centrality_weighted.nii.gz']}
    }

    file_dict = create_unique_file_dict(filepaths, output_folder, replacements)

    assert ref_output == file_dict


def create_unique_file_dict(filepaths, output_folder_path, replacements=None):

    # filepaths:
    #   list of output filepaths from a CPAC output directory
    # output_folder_path:
    #   the CPAC output directory the filepaths are from
    # replacements:
    #   (optional) a list of strings to be removed from the filepaths should
    #   they occur

    # output
    #   files_dict
    #     a dictionary of dictionaries, format:
    #     files_dict["centrality"] = 
    #         {("centrality", midpath, nums): <filepath>, ..}

    files_dict = {}

    for filepath in filepaths:

        if "_stack" in filepath:
            continue

        if ("itk" in filepath) or ("xfm" in filepath):
            continue

        path_changes = []
        real_filepath = filepath
        if replacements:
            for word_couple in replacements:
                if "," not in word_couple:
                    err = "\n\n[!] In the replacements text file, the old " \
                          "substring and its replacement must be separated " \
                          "by a comma.\n\n"
                    raise Exception(err)
                word = word_couple.split(",")[0]
                new = word_couple.split(",")[1]
                if word in filepath:
                    path_changes.append("old: {0}".format(filepath))
                    filepath = filepath.replace(word, new)
                    path_changes.append("new: {0}".format(filepath))

        if path_changes:
            import os
            with open(os.path.join(os.getcwd(), "path_changes.txt"), "wt") as f:
                for path in path_changes:
                    f.write(path)
                    f.write("\n")

        filename = filepath.split("/")[-1]

        # name of the directory the file is in
        folder = filepath.split("/")[-2]

        midpath = filepath.replace(output_folder_path, "")
        midpath = midpath.replace(filename, "")

        # name of the output type/derivative
        try:
            category = midpath.split("/")[2]
        except IndexError as e:
            continue

        if "eigenvector" in filepath:
            category = category + ": eigenvector"
        if "degree" in filepath:
            category = category + ": degree"
        if "lfcd" in filepath:
            category = category + ": lfcd"

        # this provides a way to safely identify the specific file
        # without relying on a full string of the filename (because
        # this can change between versions depending on what any given
        # processing tool appends to output file names)
        nums_in_folder = [int(s) for s in folder if s.isdigit()]
        nums_in_filename = [int(s) for s in filename if s.isdigit()]

        file_nums = ''

        for num in nums_in_folder:
            file_nums = file_nums + str(num)

        for num in nums_in_filename:
            file_nums = file_nums + str(num)

        # load these settings into the tuple so that the file can be
        # identified without relying on its full path (as it would be
        # impossible to match files from two regression tests just
        # based on their filepaths)
        file_tuple = (category, midpath, file_nums)

        temp_dict = {}
        temp_dict[file_tuple] = [real_filepath]

        if category not in files_dict.keys():
            files_dict[category] = {}

        files_dict[category].update(temp_dict)

    return files_dict


def test_match_filepaths():

    from cpac_correlations_wf import match_filepaths

    old_files_dict = {
      'alff_to_standard_smooth':
        {('alff_to_standard_smooth', 
          '/sub002/alff_to_standard_smooth/_scan_rest_1/', '1'):
            ['/old_run/sub002/alff_to_standard_smooth/_scan_rest_1/file.nii.gz']},
      'centrality_outputs: degree': 
        {('centrality_outputs: degree', 
          '/sub001/centrality_outputs/_scan_rest_1/', '1'): 
            ['/old_run/sub001/centrality_outputs/_scan_rest_1/degree_centrality_weighted.nii.gz']},
      'centrality_outputs: eigenvector': 
        {('centrality_outputs: eigenvector', 
          '/sub001/centrality_outputs/_scan_rest_1/', '1'):
            ['/old_run/sub001/centrality_outputs/_scan_rest_1/eigenvector_centrality_weighted.nii.gz']}
    }

    new_files_dict = {
      'alff_to_standard_smooth':
        {('alff_to_standard_smooth', 
          '/sub002/alff_to_standard_smooth/_scan_rest_1/', '1'):
            ['/new_run/sub002/alff_to_standard_smooth/_scan_rest_1/file.nii.gz']},
      'centrality_outputs: degree': 
        {('centrality_outputs: degree', 
          '/sub001/centrality_outputs/_scan_rest_1/', '1'): 
            ['/new_run/sub001/centrality_outputs/_scan_rest_1/degree_centrality_weighted.nii.gz']},
      'centrality_outputs: eigenvector': 
        {('centrality_outputs: eigenvector', 
          '/sub001/centrality_outputs/_scan_rest_1/', '1'):
            ['/new_run/sub001/centrality_outputs/_scan_rest_1/eigenvector_centrality_weighted.nii.gz']}
    }

    # the output should be similar to the inputs, except the two input
    # dictionaries have been merged
    ref_output_dict = {
      'alff_to_standard_smooth': 
        {('alff_to_standard_smooth',
          '/sub002/alff_to_standard_smooth/_scan_rest_1/', '1'): 
            ['/old_run/sub002/alff_to_standard_smooth/_scan_rest_1/file.nii.gz',
             '/new_run/sub002/alff_to_standard_smooth/_scan_rest_1/file.nii.gz']},
      'centrality_outputs: degree': 
        {('centrality_outputs: degree',
          '/sub001/centrality_outputs/_scan_rest_1/', '1'): 
            ['/old_run/sub001/centrality_outputs/_scan_rest_1/degree_centrality_weighted.nii.gz',
             '/new_run/sub001/centrality_outputs/_scan_rest_1/degree_centrality_weighted.nii.gz']},
      'centrality_outputs: eigenvector': 
        {('centrality_outputs: eigenvector',
          '/sub001/centrality_outputs/_scan_rest_1/', '1'): 
            ['/old_run/sub001/centrality_outputs/_scan_rest_1/eigenvector_centrality_weighted.nii.gz',
             '/new_run/sub001/centrality_outputs/_scan_rest_1/eigenvector_centrality_weighted.nii.gz']}
    }

    output_dict = match_filepaths(old_files_dict, new_files_dict)

    assert ref_output_dict == output_dict


def match_filepaths(old_files_dict, new_files_dict):
    """Returns a dictionary mapping each filepath from the first CPAC run to the
    second one, matched to derivative, strategy, and scan.

    old_files_dict: each key is a derivative name, and each value is another
                    dictionary keying (derivative, mid-path, last digit in path)
                    tuples to a list containing the full filepath described by
                    the tuple that is the key
    new_files_dict: same as above, but for the second CPAC run

    matched_path_dict: same as the input dictionaries, except the list in the
                       sub-dictionary value has both file paths that are matched
    """

    # file path matching
    matched_path_dict = {}
    missing_in_old = []
    missing_in_new = []

    for key in new_files_dict:
        # for types of derivative...
        if key in old_files_dict.keys():
            for file_id in new_files_dict[key]:
                if file_id in old_files_dict[key].keys():

                    if key not in matched_path_dict.keys():
                        matched_path_dict[key] = {}

                    matched_path_dict[key][file_id] = \
                        old_files_dict[key][file_id] + new_files_dict[key][file_id]

                else:
                    missing_in_old.append(file_id)#new_files_dict[key][file_id])
        else:
            missing_in_old.append(new_files_dict[key])

    # find out what is in the last version's outputs that isn't in the new
    # version's outputs
    for key in old_files_dict:
        if new_files_dict.get(key) != None:
            missing_in_new.append(old_files_dict[key])

    if len(matched_path_dict) == 0:
        err = "\n\n[!] No output paths were successfully matched between " \
              "the two CPAC output directories!\n\n"
        raise Exception(err)

    return matched_path_dict #, missing_in_old, missing_in_new


def test_calculate_correlation_no_s3():

    pass


def calculate_correlation(args_tuple):

    import os
    import subprocess
    import nibabel as nb
    import numpy as np
    import scipy.stats.mstats
    import scipy.stats
    import math

    from cpac_correlations_wf import download_from_s3, concordance
   
    category = args_tuple[0]
    old_path = args_tuple[1]
    new_path = args_tuple[2]
    local_dir = args_tuple[3]
    s3_creds = args_tuple[4]

    print "Calculating correlation between %s and %s" % (old_path, new_path)

    corr_tuple = None

    if s3_creds:
        try:
            # full filepath with filename
            old_local_file = os.path.join(local_dir, "s3_input_files", \
                old_path.replace("s3://",""))
            # directory without filename
            old_local_path = old_local_file.replace(old_path.split("/")[-1],"")

            new_local_file = os.path.join(local_dir, "s3_input_files", \
                new_path.replace("s3://",""))
            new_local_path = new_local_file.replace(new_path.split("/")[-1],"")

            if not os.path.exists(old_local_path):
                os.makedirs(old_local_path)
            if not os.path.exists(new_local_path):
                os.makedirs(new_local_path)

        except Exception as e:
            err = "\n\nLocals: %s\n\n[!] Could not create the local S3 " \
                  "download directory.\n\nError details: %s\n\n" \
                  % (locals(), e)
            raise Exception(e)

        try:
            if not os.path.exists(old_local_file):
                old_path = download_from_s3(old_path, old_local_path, s3_creds)
            else:
                old_path = old_local_file
        except Exception as e:
            err = "\n\nLocals: %s\n\n[!] Could not download the files from " \
                  "the S3 bucket. \nS3 filepath: %s\nLocal destination: %s" \
                  "\nS3 creds: %s\n\nError details: %s\n\n" \
                  % (locals(), old_path, old_local_path, s3_creds, e)
            raise Exception(e)

        try:
            if not os.path.exists(new_local_file):
                new_path = download_from_s3(new_path, new_local_path, s3_creds)
            else:
                new_path = new_local_file
        except Exception as e:
            err = "\n\nLocals: %s\n\n[!] Could not download the files from " \
                 "the S3 bucket. \nS3 filepath: %s\nLocal destination: %s" \
                  "\nS3 creds: %s\n\nError details: %s\n\n" \
                  % (locals(), new_path, new_local_path, s3_creds, e)
            raise Exception(e)

    ## nibabel to pull the data from the re-assembled file paths
    if os.path.exists(old_path) and os.path.exists(new_path):

        if ('roi_stats.csv' in old_path and 'roi_stats.csv' in new_path) or \
                ('spatial_map_timeseries.txt' in old_path and 'spatial_map_timeseries.txt' in new_path) or \
                    ('.1D' in old_path and '.1D' in new_path):

            try:
                old_csv = []
                new_csv = []

                with open(old_path, 'r') as f:
                    old_rois = f.readlines()
                with open(new_path, 'r') as f:
                    new_rois = f.readlines()
            except:
                corr_tuple = ("file reading problem", old_path, new_path)
                return corr_tuple

            try:
                for line in old_rois:
                    if '#' not in line:
                        new_row = [float(x.rstrip('\n')) for x in line.split('\t') if x != '']
                        old_csv.append(new_row)

                for line in new_rois:
                    if '#' not in line:
                        new_row = [float(x.rstrip('\n')) for x in line.split('\t') if x != '']
                        new_csv.append(new_row)

                data_1 = np.asarray(old_csv)
                data_2 = np.asarray(new_csv)
            except:
                corr_tuple = ("file processing problem", old_path, new_path)
                return corr_tuple

        else:
            try:
                raw_file_img = nb.load(old_path)
                raw_file_hdr = raw_file_img.get_header()
                roi_mask_img = nb.load(new_path)
                roi_mask_hdr = roi_mask_img.get_header()

                raw_file_dims = raw_file_hdr.get_zooms()
                roi_mask_dims = roi_mask_hdr.get_zooms()
  
                if raw_file_dims != roi_mask_dims:

                    old_path_dir = old_path.split(os.path.basename(old_path))[0]

                    resampled_outfile = os.path.join(old_path_dir, \
                                                     "resampled_%s" \
                                                     % os.path.basename(old_path))

                    if os.path.exists(resampled_outfile):
                        old_path = resampled_outfile
                    else:
                        resample_str = ["flirt", "-in", old_path, "-ref", new_path, \
                                        "-applyisoxfm", str(roi_mask_dims[0]), "-interp", \
                                        "trilinear", "-out", resampled_outfile]

                        try:
                            retcode = subprocess.check_output(resample_str)
                        except Exception as e:
                            err = "\n\n[!] Something went wrong with running FSL FLIRT for " \
                                  "the purpose of resampling the custom ROI mask to match " \
                                  "the original output file's resolution.\n\nCustom ROI " \
                                  "mask file: %s\n\nError details: %s\n\n" % (roi_mask, e)
                            raise Exception(err)

                        old_path = resampled_outfile

                data_1 = nb.load(old_path).get_data()
                data_2 = nb.load(new_path).get_data()

            except:
                corr_tuple = ("file reading problem", old_path, new_path)
                return corr_tuple

        ## set up and run the Pearson correlation and concordance correlation
        if data_1.flatten().shape == data_2.flatten().shape:
            try:
                pearson = scipy.stats.pearsonr(data_1.flatten(), data_2.flatten())[0]
                concor = concordance(data_1.flatten(), data_2.flatten(), pearson)
            except:
                corr_tuple = ("correlating problem", old_path, new_path)
                return corr_tuple
            if concor > 0.980:
                corr_tuple = (category, [concor])
            else:
                corr_tuple = (category, [concor], (old_path, new_path))
            print "Success - %s" % str(concor)
        else:
            corr_tuple = ("different shape", old_path, new_path)

    else:
        if not os.path.exists(old_path):
            corr_tuple = ("file doesn't exist", [old_path], None)
        if not os.path.exists(new_path):
            if not corr_tuple:
                corr_tuple = ("file doesn't exist", [new_path], None)
            else:
                corr_tuple = ("file doesn't exist", old_path, new_path)

    return corr_tuple


def organize_correlations(concor_dict):

    # break up all of the correlations into groups - each group of derivatives
    # will go into its own boxplot

    regCorrMap = {}
    native_outputs = {}
    template_outputs = {}
    functionals = {}

    corr_map_dict = {}
    corr_map_dict["correlations"] = {}

    derivs = ['alff', 'dr_tempreg', 'reho', 'sca_roi', 'timeseries']
    anats = ['anatomical', 'seg']
    funcs = ['functional', 'motion_correct', 'slice']

    for key in concor_dict:

        if 'xfm' in key or 'mixel' in key:
            continue

        if 'centrality' in key or 'vmhc' in key or 'sca_tempreg' in key:
            template_outputs[key] = concor_dict[key]
            continue

        for word in anats:
            if word in key:
                regCorrMap[key] = concor_dict[key]
                continue

        for word in derivs:
            if word in key and 'standard' not in key:
                native_outputs[key] = concor_dict[key]
                continue
            elif word in key:
                template_outputs[key] = concor_dict[key]
                continue

        for word in funcs:
            if word in key:
                functionals[key] = concor_dict[key]

    if len(regCorrMap.values()) > 0:
        corr_map_dict["correlations"]['concordance_registration_and_segmentation'] = regCorrMap

    if len(native_outputs.values()) > 0:
        corr_map_dict["correlations"]['concordance_native_space_outputs'] = native_outputs

    if len(template_outputs.values()) > 0:
        corr_map_dict["correlations"]['concordance_template_space_outputs'] = template_outputs

    if len(functionals.values()) > 0:
        corr_map_dict["correlations"]['concordance_functional_outputs'] = functionals

    return corr_map_dict


def create_boxplot(corr_group, corr_group_name, pipeline_names=None,
                   current_dir=None):

    import os
    import numpy as np
    from matplotlib import pyplot

    if not pipeline_names:
        pipeline_names = ["pipeline_1", "pipeline_2"]
    if not current_dir:
        current_dir = os.getcwd()

    allData = []
    labels = corr_group.keys()
    labels.sort()

    for label in labels:
        if "file reading problem" in label:
            continue
        try:
            allData.append(np.asarray(corr_group[label]).astype(np.float))
        except ValueError as ve:
            print label
            raise Exception(ve)

    pyplot.boxplot(allData)
    pyplot.xticks(range(1,(len(corr_group)+1)),labels,rotation=85)
    pyplot.margins(0.5,1.0)
    pyplot.xlabel('Derivatives')
    pyplot.title('Correlations between %s and %s\n '
                 '( %s )' % (pipeline_names[0], pipeline_names[1],
                             corr_group_name))

    output_filename = os.path.join(current_dir,
                                   (corr_group_name + "_" +
                                    pipeline_names[0] +
                                    "_and_" + pipeline_names[1]))

    pyplot.savefig('%s.pdf' % output_filename, format='pdf', dpi=200, bbox_inches='tight')
    pyplot.close()


def test_aggregate_correlations():

    correlation_info_list = \
        [("anatomical_brain", 1.0, 1.0), ("anatomical_brain", 0.95, 0.89), \
         ("anatomical_brain", 0.67,0.50), ("alff_img", 0.98, 0.96), \
         ("alff_img", 0.82, 0.80)]

    ref_pearson_dict = \
        {"anatomical_brain": [1.0, 0.95, 0.67], "alff_img": [0.98, 0.82]}
    ref_concor_dict = \
        {"anatomical_brain": [1.0, 0.89, 0.50], "alff_img": [0.96, 0.80]}

    pearson_dict, concor_dict = aggregate_correlations(correlation_info_list)

    assert ref_pearson_dict == pearson_dict
    assert ref_concor_dict == concor_dict


def main():

    import os
    import argparse

    from multiprocessing import Pool
    import itertools

    parser = argparse.ArgumentParser()

    parser.add_argument("--old_outputs_path", type=str, \
                            help="path to a CPAC outputs directory - the " \
                                 "folder containing the participant-ID " \
                                 "labeled directories")

    parser.add_argument("--new_outputs_path", type=str, \
                            help="path to a CPAC outputs directory - the " \
                                 "folder containing the participant-ID " \
                                 "labeled directories")
                                 
    parser.add_argument("num_cores", type=int, \
                            help="number of cores to use - will calculate " \
                                 "correlations in parallel if greater than 1")

    parser.add_argument("run_name", type=str, \
                            help="name for the correlations run")

    parser.add_argument("--s3_creds", type=str, \
                            help="path to your AWS S3 credentials file")

    parser.add_argument("--replacements", type=str, \
                            help="text file containing strings you wish to " \
                                 "have removed from the filepaths if they " \
                                 "occur - place one on each line")

    parser.add_argument("--corr_map", type=str,
                        help="YAML file with already-calculated "
                             "correlations, which can be provided if you "
                             "only want to generate the box plots again")

    args = parser.parse_args()

    # run it!
    if args.old_outputs_path and args.new_outputs_path:
        if args.s3_creds:
            if ("s3://" in args.old_outputs_path) and \
                    ("s3://" in args.new_outputs_path):
                old_outputs_path = args.old_outputs_path
                new_outputs_path = args.new_outputs_path
            else:
                err = "\n\n[!] If pulling output files from an S3 bucket, the "\
                      "output folder paths must have the s3:// prefix.\n\n"
                raise Exception(err)
        else:
            old_outputs_path = os.path.abspath(args.old_outputs_path)
            new_outputs_path = os.path.abspath(args.new_outputs_path)

        pipeline_names = [old_outputs_path.split('/')[-1], \
                          new_outputs_path.split('/')[-1]]

    if args.replacements:
        replacements = read_txt_file(os.path.abspath(args.replacements))
    else:
        replacements = None

    output_dir = os.path.join(os.getcwd(), "correlations_%s" % args.run_name)

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except:
            err = "\n\n[!] Could not create the output directory for the " \
                  "correlations. Do you have write permissions?\nAttempted " \
                  "output directory: %s\n\n" % output_dir
            raise Exception(err)

    if args.corr_map:
        corr_map_dict = read_pickle(args.corr_map)

        for corr_group_name in corr_map_dict["correlations"].keys():
            corr_group = corr_map_dict["correlations"][corr_group_name]
            create_boxplot(corr_group, corr_group_name,
                           corr_map_dict["pipeline_names"], output_dir)

    else:

        # last regression test
        output_yml = os.path.join(output_dir, "%s_old_files.yml" % pipeline_names[0])

        matched_path_file = os.path.join(output_dir, "matched_path_dict.yml")

        if os.path.exists(matched_path_file):
            matched_path_dict = read_yml_file(matched_path_file)
        else:
            matched_path_dict = None

            if os.path.exists(output_yml):
                print "Found output list YAML for pipeline %s, skipping output file" \
                      "path parsing.." % pipeline_names[0]
                old_files_dict = read_yml_file(output_yml)
            else:
                if args.s3_creds:
                    old_files_list = pull_NIFTI_file_list_from_s3(old_outputs_path, args.s3_creds)
                else:
                    old_files_list = gather_filepaths(old_outputs_path)

                old_files_dict = create_unique_file_dict(old_files_list, \
                    old_outputs_path, replacements)

                write_yml_file(old_files_dict, output_yml)

            # this regression test
            output_yml = os.path.join(output_dir, "%s_new_files.yml" % pipeline_names[1])

            if os.path.exists(output_yml):
                print "Found output list YAML for pipeline %s, skipping output file" \
                      "path parsing.." % pipeline_names[1]
                new_files_dict = read_yml_file(output_yml)
            else:
                if args.s3_creds:
                    new_files_list = pull_NIFTI_file_list_from_s3(new_outputs_path, args.s3_creds)
                else:
                    new_files_list = gather_filepaths(new_outputs_path)

                new_files_dict = create_unique_file_dict(new_files_list, \
                    new_outputs_path, replacements)

                write_yml_file(new_files_dict, output_yml)

            matched_path_dict = match_filepaths(old_files_dict, new_files_dict)

            write_yml_file(matched_path_dict, matched_path_file)

        all_corr_dict = {}
        full_corr_dict = {}
        sub_opt_dct = {}

        args_list = []

        # load full corr yaml dict
        full_corr_file = os.path.join(output_dir, "full_corr_dict.yml")

        if os.path.exists(full_corr_file):
            full_corr_dict = read_yml_file(full_corr_file)

        for category in matched_path_dict.keys():

            for file_id in matched_path_dict[category].keys():

                #if file_id in full_corr_dict.keys():
                #    if file_id[0] not in all_corr_dict.keys():
                #        all_corr_dict[file_id[0]] = full_corr_dict[file_id]
                #    continue

                old_path = matched_path_dict[category][file_id][0]
                new_path = matched_path_dict[category][file_id][1]

                #if (".nii" not in old_path) or (".nii" not in new_path):
                #    print "Skipping %s and %s" % (old_path, new_path)
                #    continue

                args_list.append((category, old_path, new_path, output_dir, args.s3_creds))

        print "\nNumber of correlations to calculate: %d\n" % len(args_list)

        from cpac_correlations_wf import calculate_correlation

        p = Pool(args.num_cores)
        corr_tuple_list = p.map(calculate_correlation, args_list)

        for corr_tuple in corr_tuple_list:

            if corr_tuple[0] not in all_corr_dict.keys():
                all_corr_dict[corr_tuple[0]] = []

            all_corr_dict[corr_tuple[0]] += corr_tuple[1]

            if len(corr_tuple) > 2:
                if corr_tuple[0] not in sub_opt_dct:
                    sub_opt_dct[corr_tuple[0]] = []
                try:
                    sub_opt_dct[corr_tuple[0]].append("{0}:\n{1}\n{2}\n\n".format(corr_tuple[1][0], corr_tuple[2][0], corr_tuple[2][1]))
                except TypeError:
                    pass
                
            #if file_id not in full_corr_dict.keys():
            #    full_corr_dict[file_id] = []

            #full_corr_dict[file_id].append(corr_tuple[1])

        #write_yml_file(full_corr_dict, full_corr_file)

        # let's go
        corr_map_dict = organize_correlations(all_corr_dict)
        corr_map_dict["pipeline_names"] = pipeline_names

        write_pickle(corr_map_dict, os.path.join(output_dir, "corr_map_dict.p"))

        if sub_opt_dct:
            write_yml_file(sub_opt_dct, os.path.join(output_dir, "sub_optimal.yml"))

        for corr_group_name in corr_map_dict["correlations"].keys():
            corr_group = corr_map_dict["correlations"][corr_group_name]
            create_boxplot(corr_group, corr_group_name,
                           corr_map_dict["pipeline_names"], output_dir)


if __name__ == "__main__":
    main()