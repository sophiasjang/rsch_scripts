#!/usr/bin/python

'''
This script
- takes any number of notebooks to be processed as arguments
- converts each notebook into a HTML document,
- searches for links to local files in the same or a subfolder of the notebook,
- compresses the HTML document and the local files into a tar.gz
- copies the tar.gz to altvater@ssh.ocf.berkeley.edu
'''

import sys
import os
import re
import shutil
from subprocess import Popen, PIPE
from bs4 import BeautifulSoup
import textwrap

args = sys.argv[1:]

delete_tmp = True
ssh = True

if "--debug" in args:
    args.pop(args.index("--debug"))
    delete_tmp = False
if "--nossh" in args:
    args.pop(args.index("--nossh"))
    ssh = False
    delete_tmp = False

notebooks = args

tmp_paths = []
for nb in notebooks:
    print
    print nb
    wrapper = textwrap.TextWrapper(initial_indent="  ", subsequent_indent="      ")
    nb_name = os.path.splitext(os.path.basename(nb))[0]
    nb_folder = os.path.dirname(nb)
    # list of path names to delete at the end
    
    # make new folder for html documents within notebook folder
    html_dir = os.path.normpath(os.path.join(nb_folder, nb_name))
    if os.path.exists(html_dir):
        choice = raw_input("  Overwriting {}? ([y]/n)".format(html_dir))
        if choice.lower() in ('n', 'no', 'nein'):
            print "  Not processing {}.".format(nb)
            continue
        try:
            shutil.rmtree(html_dir)
        except OSError as e:
            print "  OSError: ", e
            continue
    try:
        os.mkdir(html_dir)
        tmp_paths.append(html_dir)
    except OSError as e:
        print "  OSError: ", e
        continue
    
    # copy exclude_preprocessor and ipython_nbconvert_config.py into current folder
    # copy ipython custom.css to folder
    #for source in ("/home/flo/Eigene/a_research/scripts/notebook/exclude_preprocessor.py",
                   #"/home/flo/Eigene/a_research/scripts/notebook/ipython_nbconvert_config.py"):
        #try:
            #dest = os.path.abspath(os.path.join(".", os.path.basename(source)))
            #shutil.copy2(source, dest)
            #tmp_paths.append(dest)
        #except IOError as e:
            #print "  IOError: ", e
            #print "  Not excluding selected input and output cells."
    #tmp_paths.append("/home/flo/Eigene/a_research/scripts/notebook/exclude_preprocessor.pyc")
    # convert notebook into html document
    #print "  Converting to html:"
    
    html = os.path.join(html_dir, "index.html")
    
    cmd = ["ipython", "nbconvert", "--quiet", "--to", "html", "--template", "exclude_html.tpl",
           "--output={}".format(os.path.splitext(html)[0]), nb]
    print wrapper.fill(" ".join(cmd))
    (stdout, stderr) = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    if stdout:
        for line in stdout.splitlines():
            print wrapper.fill(line)
    if stderr:
        for line in ('ERROR:\n'+stdout).splitlines():
            print wrapper.fill(line)

    # search for url links to local files
    soup = BeautifulSoup(open(html, "r"))
    links = set()
    for tag in soup.find_all('a'):
        if tag.get("href"):
            links.add(tag.get("href"))
    for tag in soup.find_all('img'):
        if tag.get("src"):
            links.add(tag.get("src"))
    
    links = sorted(links)
    if links:
        # check if basenames are unique as all files will be copied into same directory
        # if two basenames are the same the parent folder/s is/are prepended
        # with "_" until all basenames are unique
        abspaths = []
        copying = []
        no_files = []
        for l in links:
            abspath = os.path.abspath(os.path.join(nb_folder, l))
            if os.path.exists(abspath):
                abspaths.append(abspath)
                copying.append(l) #'{} -> "{}"'.format(l, abspath))
            else:
                if l.startswith("#") or l.startswith("data:image"):
                    # header lines start with #
                    # embedded images start with data:image (probably)
                    pass
                else:
                    no_files.append(l)
        
        if copying:
            print "  Copying the following links:"
            print "    " + "\n    ".join(copying)
        if no_files:
            print "  No files found for the following links:"
            print "    " + "\n    ".join(no_files)
        
        if abspaths:
            basenames = list(map(os.path.basename, abspaths))
            doubles = set([x for x in basenames if basenames.count(x) > 1])
            
            pos = -2
            while doubles:
                for i, bn in enumerate(basenames):
                    if bn in doubles:
                        new = os.path.join(*abspaths[i].split(os.sep)[pos:])
                        basenames[i] = new.replace(os.sep, '_')
                doubles = set([x for x in basenames if basenames.count(x) > 1])
                pos -= 1
            
            # create directory to copy local files into
            links_dir = os.path.normpath(os.path.join(html_dir, "files"))
            try:
                os.mkdir(links_dir)
            except OSError as e:
                print "  OSError: ", e
                continue
            
            dest_paths = [os.path.join(links_dir, bn) for bn in basenames]
            # now copy all local_files into the html/files folder
            for source, dest in zip(abspaths, dest_paths):
                try:
                    shutil.copy2(source, dest)
                except IOError as e:
                    print "  IOError: ", e
                    continue
            
            # finally replace all links within the html file with the new basenames
            new = [os.path.join("files", bn) for bn in basenames]
            link_map = dict(zip(copying, new))
            # replace links with new basenames, or leave in place if not in link_map
            for tag in soup.find_all('a'):
                tag["href"] = link_map.get(tag.get("href"), tag.get("href"))
            for tag in soup.find_all('img'):
                tag["src"] = link_map.get(tag.get("src"), tag.get("src"))
    
    destroy = []
    for tag in soup.find_all("div", class_=re.compile("exclude_input|exclude_output")):
        cell = tag.find("div", class_=re.compile("code_cell|text_cell"))
        if cell:
            if (("exclude_input" in tag["class"] and "exclude_output" in tag["class"])
               or "text_cell" in cell["class"]):
                # delete whole cell
                destroy.append(tag)
            else:
                # delete "input" and "output_wrapper" and delete the prompt string
                # deleting the prompt tags leads to unindention of the respective remaining cells
                p = None
                if "exclude_input" in tag["class"]:
                    destroy.append(cell.find("div", class_="input"))
                    p = cell.find("div", class_="output_prompt")
                elif "exclude_output" in tag["class"]:
                    destroy.append(cell.find("div", class_="output_wrapper"))
                    p = cell.find("div", class_="input_prompt")
                if p:
                    p.string = ""
    
    # delete excluded cells
    delete = True
    for tag in destroy:
        if tag:
            if delete:
                tag.decompose()
            else:
                tag["style"] = "display: none;"
    
                
            #parent["style"] = "display: none;"
        ## hide corresponding "Out [n]:" as well
        #output_prompt = tag.find_next("div", class_="prompt output_prompt")
        #if output_prompt:
            #output_prompt.string = ""
    
    #for tag in soup.find_all(text=re.compile(".*#hide_output.*")):
        #parent = tag.find_parent("div", class_="output_wrapper")
        #if parent:
            #parent["style"] = "display: none;"
        #else:
            ## if no parent was found, #hide_output was probably in input cell.
            ## Therefore hide corresponding output. If next input is found first
            ## do nothing
            #output = tag.find_next("div", class_=re.compile("^input$|^output_wrapper$"))
            #if output and "output_wrapper" in output["class"]:
                #output["style"] = "display: none;"
            
    # write html soup back to file
    with open(html, "w") as fout:
        text = soup.prettify().encode('utf-8')
        # clean up code
        # emtpy hrefs are inserted by BeautifulSoup when no href URL is given.
        # But that screws up the spoiler links.
        text = text.replace(" href ", " ")
        fout.write(text)
    
    # copy ipython custom.css to folder
    source = "/home/flo/.ipython/profile_default/static/custom/custom.css"
    dest = os.path.join(html_dir, "custom.css")
    print "  Copying custom.css from:"
    print "    " + source
    shutil.copy2(source, dest)
    
    
    if ssh:
        # sync html document and files to ocf server
        cmd = ["rsync", "-az", "-e", "ssh", "--delete", html_dir.rstrip(os.sep), 
            "altvater@ssh.ocf.berkeley.edu:~/public_html/private/notebooks/"]
        print wrapper.fill(" ".join(cmd))
        (stdout, stderr) = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        if stdout:
            for line in stdout.splitlines():
                print wrapper.fill(line)
        if stderr:
            for line in ('ERROR:\n'+stdout).splitlines():
                print wrapper.fill(line)
        
        # set rights on the server
        cmd = ["ssh", "altvater@ssh.ocf.berkeley.edu", 
            'bin/set_notebook_rights.sh "public_html/private/notebooks/{}"'.format(nb_name)]
        print wrapper.fill(" ".join(cmd))
        (stdout, stderr) = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        if stdout:
            for line in stdout.splitlines():
                print wrapper.fill(line)
        if stderr:
            for line in ('ERROR:\n'+stdout).splitlines():
                print wrapper.fill(line)
    
# cleanup
if delete_tmp:
    print "  Cleaning up."
    for path in tmp_paths:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except OSError as e:
                print "  OSError: ", e
                continue
                
