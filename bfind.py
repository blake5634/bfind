#!/usr/bin/python3

import os
import re
import subprocess as sub
import sys
import argparse as ap
import pyperclip


args = sys.argv
shntool = '/home/blake/bin/docgui4'
latextool = '/home/blake/bin/latui4'
pdftool = '/usr/bin/okular'
worddoctool = '/usr/bin/libreoffice'
sheettool = '/usr/bin/libreoffice'
pptool = '/usr/bin/libreoffice'
textfiletool = '/usr/bin/kate'
cpptool = '/usr/bin/kate'
pythontool = '/usr/bin/kate'
perltool = '/usr/bin/kate'
pictool = '/usr/bin/gwenview'
videotool = '/usr/bin/vlc'
mdtool = textfiletool

tools = {'.pdf':pdftool, '.docx':worddoctool, '.odt':worddoctool, '.shn':shntool,
         '.xlsx':sheettool, '.xls':sheettool, '.ods':sheettool,
         '.txt':textfiletool, '.tex':latextool,
         '.cpp':cpptool, '.c':cpptool, '.h':cpptool,
         '.ino':cpptool,  '.py':pythontool, '.pl':perltool, '.md':mdtool,
         '.png':pictool, '.jpg':pictool, '.mpg':videotool, '.mp4':videotool,
         '.svg':'inkscape', '.ppt':pptool}


maxResults = 25
dateSort = False

#
#   build argparser
#

# consider support for these other cool options:
#https://phoenixnap.com/kb/locate-command-in-linux

aparse = ap.ArgumentParser(prog='blocate.py',
            description='A more powerful version of locate command',
            epilog='')

aparse.add_argument('searchTerms', metavar='term', type=str,nargs='+',
                    help="A search term. Multiple terms are AND'ed together")

aparse.add_argument('-v', metavar='term', type=str,nargs='+',
                    help='Eliminate the next search term from results (grep -v)')

aparse.add_argument('--Case',  dest='case', action='store_true',
                    help="Be case sensitive (default not case sensitive)")

aparse.add_argument('--home',  dest='home', action='store_true',
                    help="Automatically limit the search to the user's home dir")

aparse.add_argument('--cmd',  dest='cmd', action='store_true',
                    help="Print the command line generated for the search")

aparse.add_argument('--update',  dest='update', action='store_true',
                    help="Update the locate database (requires password).")

aparse.add_argument('--dirs',  dest='dirs', action='store_true',
                    help='Only print directories which match or have matching files (but not the files)')

aparse.add_argument('--dots', dest='dots', action='store_true',
                    help ='Show hidden directories like ".cache" etc.')


aparse.add_argument('--date', dest='date', action='store_true',
                    help= 'Show and sort by modification date')
#
#   Pre-process the arg flist to hide the -v options(!)#_#_(__
#
flipnext = False
newargs = []
prefix = '**NNNNNNNNNNN**' # note this precludes certain search terms!!
for a in sys.argv:
    if flipnext:
        if a == '-v':
            print('Command Line error:  no "-v -v"!')
            quit()
        newargs.append(prefix+a)  # to be flipped with 'grep -v arg'
        flipnext=False
    elif a == '-v':
        flipnext = True
    else:
        newargs.append(a)  # non flipped: 'grep arg'

#
#   work on the arguments
#

args = aparse.parse_args(newargs)

#print('Args: ', args)

args.searchTerms = args.searchTerms[1:]  # drop program name
#
#  update DB if asked
#
if args.update:
    tmp = sub.check_output('sudo updatedb',shell=True)
    if len(args.searchTerms) == 0:
        quit()
#
#  process -v modifiers
#

negNext = False
grepTerms = []
for term in args.searchTerms:
    if negNext:
        grepTerms.append('-v '+term)
        negNext = False
    if term == '-v':
        negNext = True
    else:
        grepTerms.append(term)


homedir = 'unknown'
if args.home:
    homedir = str(sub.check_output('echo $HOME',shell=True)[:-1].decode('UTF-8'))


#
#  Some utilities
#

def get_mod_date_ls_format(filepath): # thanks Claude!
    try:
        result = sub.run(['ls', '-lt', '--time-style=long-iso', filepath],
                          capture_output=True, text=True, check=True)
        parts = result.stdout.strip().split()
        return f"{parts[5]} {parts[6]}"  # Returns: YYYY-MM-DD HH:MM
    except:
        return 'deleted file'

def pfiles(flist, nmax, datesort=False, ddict={}):
    if datesort and ddict is not None:
        flist.sort(key=lambda x: ddict[x]) # thanks Claude!
    nf = len(flist)
    if nf > nmax:
        print(f'Too many results ({nf}) ... first {nmax} are:')
        flist = flist[:nmax]
    i=0
    for path in flist:
        i+=1
        if datesort:
            print(f'{i:3} {ddict[path]} {path}')
        else:
            print(f'{i:3}  {path}')

#print("Home: ",homedir)
#print("Search Term(s)")
#print(args.searchTerm)

if args.case:
    cmd = 'locate '
    grepOpt = ''
else:  # default is case insensitive
    cmd = 'locate -i '
    grepOpt = '-i'

i=0
for a in grepTerms:
        if a.startswith(prefix):   # restore the -v option modifer for grep
            a = '-v '+ a[len(prefix):]
        if i==0:
            cmd += a + ' '
        else:
            cmd += f'| grep {grepOpt} {a} '
        i+=1
        #print(f'{i:3} {a}')


if homedir != 'unknown':
    cmd += f'| grep {homedir}  '

if args.cmd:
    print("Command: ",cmd)

#rawres = sub.check_output(cmd,shell=True)
try:
    rawres = sub.check_output(cmd,shell=True)
except sub.CalledProcessError as grepexc:
    print("Sorry, there were no results")
    quit()
# Parse the output as a flist of strings
lines = rawres.decode("utf-8").splitlines()

i=0
prevline = 'aldjflawe8203498ijcmk'
dirs = []

if not args.dots:  # eliminate .files and .dirs  unless --dots option.
    l2 = []
    for l in lines:
        keep = True
        dirs = l.split('/')
        for dname in dirs:
            # print(' dname: ', dname, keep)
            if dname.startswith('.'):
                keep = False
        if keep:
            l2.append(l)
    lines = l2

ddates = {}
if args.date:        #   sort by and print mod date of each file
    ddates = {}
    for l in lines:
        ddates[l] = get_mod_date_ls_format(l)
    dateSort = True

if args.dirs:
    # scan for the dirs
    for l in lines:
        if l.startswith(prevline+'/'):
            dirs.append(prevline+'/')
        prevline = l
    i=0

    if len(lines) == 0:
        print('there were no matches')
        quit()

    for l in lines:
        if l[0] == '/':  # get rid of leading /
            l = l[1:]
        parts = l.split('/')
        candidate = '/'
        for p in parts[:-1]:
            candidate += p + '/'
        dirs.append(candidate)
    # deduplicate
    dirs = flist(set(dirs))

    print ('Directory Results: ')
    # print them
    pfiles(dirs,maxResults, datesort=dateSort, ddict=ddates )
    # for d in dirs:
    #     i+=1
    #     print(f'{i:3}  {d}')
    quit()

else:
    print("All Results:")
    pfiles(lines, maxResults, datesort=dateSort, ddict=ddates)
    # for l in lines:
    #     i+=1
    #     print(f'{i:3}  {l}')

#############################################################################################
#
#    Get and process user selection
#

def get_extension(filename):  # thanks Claude.ai!
    pattern = r'\.([^./\\]+)$'
    match = re.search(pattern, filename)
    return match.group() if match else None

def parseInput(txt):
    cmds = []
    # thanks Claude !
    ichoice  = int(match.group()) if (match := re.search(r'\d+', txt)) else None
    cmds = re.findall(r'[a-zA-Z]', txt)
    return ichoice, cmds

if len(lines)>0:
    print(' C - copy to cwd; M - move to cwd; D - delete; <none> copy link to paste buf.')
    choice = input('enter result number: (+C,M,D cmds)')
    if choice == '':  # no input
        quit()

    ichoice, cmds = parseInput(choice)
    if len(cmds) == 0:
        pyperclip.copy(lines[ichoice-1]) # put the choice in paste buffer
        quit()


    if 'C' in cmds or 'c' in cmds: #   Copy the selection to cwd
        fname = lines[ichoice-1]
        fname = "'"+fname+"'"
        # cmd = ['cp', fname, '.']
        cmd = 'cp '+fname+' .'
        sub.run(cmd,shell=True) #  copy the desired file
        print('file is copied to current dir.')
        quit()

    if 'M' in cmds or 'm' in cmds: #   Copy the selection to cwd
        fname = lines[ichoice-1]
        fname = "'"+fname+"'"
        # cmd = ['cp', fname, '.']
        cmd = 'mv '+fname+' .'
        sub.run(cmd,shell=True) #  copy the desired file
        print('file is moved to current dir.')
        quit()

    if 'D' in cmds or 'd' in cmds: #   Delete the selection
        fname = lines[ichoice-1]
        fname = "'"+fname+"'"
        cmd = 'rm '+fname
        x= input(f'\n Are you sure you want to delete {fname}? y/N:')
        if x=='Y' or x =='y':
           #sub.run(cmd,shell=True)
            print('SIMULATION file deleted.')
        else:
            print("delete action canceled!")
            quit()

    elif re.match(r'^\d+$',choice):   # if integer  Open the identified file by extension
        nm = lines[int(choice)-1]
        ext = get_extension(nm)
        print('Filetype: ', f'[{ext}]')
        fname = nm[1:] # drop leading / of /home...
        fname = "'"+fname+"'"
        try:
            tool = tools[ext]  # look up the program to run
        except:
            tool = None
        if tool is not None:
            print('command: ',tool, fname, ' &')
            cmd = [tool, fname] #, ' & ']
            cmd = tool+' '+fname+' & '
            sub.run(cmd,shell=True,cwd='/')
        else:
            print(f'Unknown file format: {ext}')
    else:
        print("I don't understand the choice: ", choice)
        quit()
