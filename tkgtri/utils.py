import os

#
# get next filename under the [exchange directory]. if there is no folder for filename - the folder will be created
#
def get_next_report_filename(dir, filename_mask):

    filename_mask2 = filename_mask % (dir, 0)

    directory = os.path.dirname(filename_mask2)

    try:
        os.stat(directory)

    except:
        os.mkdir(directory)
        print("New directory created:", directory)

    deals_id = 0
    while os.path.exists(filename_mask % (directory, deals_id)):
        deals_id += 1

    return deals_id