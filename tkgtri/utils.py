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


# get next filename in indexed way: if file file.txt exists so the file_0.txt will be created.. and so on
def get_next_filename_index(path):
    path = os.path.expanduser(path)

    # if not os.path.exists(path):
    #     return path

    root, ext = os.path.splitext(os.path.expanduser(path))
    directory = os.path.dirname(root)
    fname = os.path.basename(root)
    candidate = fname+ext
    index = 0
    ls = set(os.listdir(directory))
    while candidate in ls:
            candidate = "{}_{}{}".format(fname,index,ext)
            index += 1
    return os.path.join(directory, candidate)