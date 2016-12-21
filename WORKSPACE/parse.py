#!/usr/local/bin/python3

import sys
import csv
import time
from collections import Counter

# ARGUMENT SPECIFICATION ###########################################################
one = '/Users/billyoung/Dropbox/Public/pmd_out/' + str(sys.argv[1]) + '-out.csv'
two = '/Users/billyoung/Dropbox/Public/ss_bugdata/' + str(sys.argv[1]) + '-ss_bugdata.csv'
three = '/Users/billyoung/Dropbox/Public/entropy_data/' + str(sys.argv[1]) + '_metrics_entropy.csv'
out = sys.argv[2]
spread = sys.argv[3]
snapshot = int(sys.argv[4])
####################################################################################

# find matches between entropy and PMD
def entropy_dict_match(d, e, s):
    match = []
    n = 0
    for k in d:
        for dat in e:
            if dat[0] == k:
                if dat[1] in d[k]:
                    n += 1
                    match.append([k,dat[1],dat[2]])
    return n, match 

# find matches between entropy and PMD
def entropy_l_match(d, e, s):
    match = []
    n = 0
    for k in d:
        for dat in e:
            if dat[0] == k[0] and dat[1] == k[1]:
                n += 1
                match.append([dat[0],dat[1],dat[2]])
    return n, match 

# given high priority violations and matches between PMD and BUGS, find bugs and types of violations
def pmd_type_match(d,h,l):
    typeout = []
    for k in d:
        for v in d[k]:
            a = v.split("+")[0]
            b = v.split("+")[1]
            if [a,int(b)] in l:
                typeout.append(str(k))
        comm = Most_Common(typeout,10)
    numbad = 0
    for k in d:
        if k in h:
            numbad += 1
    return typeout, numbad, comm

# given a list, finds the most common element (violation type) 
def Most_Common(L,n):
    data = Counter(L)
    return data.most_common(n)

# determine depth of dictionary
def dict_size(d):
    n = 0
    d_keys = set(d.keys())
    for k in d_keys:
        for v in d[k]:
            n += 1
    return n

# looks for matches between two dictionaries of bug/violation data in the tuple (file,linenum)
def dict_cmp(d1, d2, s):
    matches = []
    num_match = 0
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    if s == 0:
        for k in intersect_keys:
            for v in d1[k]:
                if v in d2[k] and [k, v] not in matches:
                    num_match += 1
                    matches.append([k,v])
    else:
        for k in intersect_keys:
            for v in d1[k]:
                for j in range(-s,s):
                    if v+j in d2[k] and [k,v+j] not in matches:
                        num_match += 1
                        matches.append([k,v+j])
    return num_match, matches

# Usage check
if len(sys.argv) != 5:
    print("USAGE:\n\n\t./parse.py [pmd-out] [ss-data] [entropy] [results] [spread] [snapshot]\n\n\tpmd-out: CSV containing PMD output data\n\n\tss-data: CSV containing bug data\n\n\tentropy: CSV containing entropy data\n\n\tresults: CSV file to store matching bugs\n\n\tspread: desired line-radius for search (1 = +/- 1 line, 2 = +/- 2 lines, etc)\n\n\tsnapshot: 0 = ignore snapshots, 1 = parse by snapshot\n\n**All files must be in current working directory **\n")
    sys.exit()

start1 = time.time()

# SETUP


p = open(one)
csv_p = csv.reader(p)
r = open(two)
csv_r = csv.reader(r)
e = open(three)
csv_e = csv.reader(e)
print("COMPARISON OF " + str(one) + " AND " + str(two) + " AND " + str(three))

pmdlines = []
reflines = []
elines = []
ebuglines = []
nebuglines = []
typelines = []
hipri = []
hient = []
tot = 0
pmd = 0
i = -1
l = set()

# ENTROPY
for row in csv_e:
    if i == -1:
        i = 0
    else:
        newpath = str(row[2])
        newpath = newpath.replace("/","__")
        newpath = "src__main__java__" + newpath
        elines.append([newpath,int(row[3]),float(row[34])])
        l.add(newpath)
        if int(row[33]) == 1:
            ebuglines.append([newpath,int(row[3]),float(row[34])])
        if int(row[33]) == 0:
            nebuglines.append([newpath,int(row[3]),float(row[34])])
        if float(row[34]) > 5:
            hient.append([newpath,int(row[3]),float(row[34])])

buglowe = 0
sum = 0
for q in ebuglines:
    sum += q[2]
    if q[2] < 5:
        buglowe += 1
avgent = sum/len(ebuglines)
sum = 0
for q in nebuglines:
    sum += q[2]
avgnent = sum/len(nebuglines)

print("\n<< ENTROPY >>")
print("Files interpreted:             " + str(len(l)))
print("Lines interpreted:             " + str(len(elines)))
print("Buggy lines:                   " + str(len(ebuglines)))
print("Non-buggy lines:               " + str( len(elines)-len(ebuglines)))
print("Buggy high entropy lines:      " + str(len(ebuglines)-buglowe))
print("Buggy low entropy lines:       " + str(buglowe))
print("Non-buggy high entropy lines:  " + str(len(hient) - (len(ebuglines)-buglowe)))
print("Non-buggy low entropy lines:   " + str( len(elines) - len(hient) - buglowe  ))
print("Average entropy of bug lines:  " + '{0:.4f}'.format( avgent))
print("Average entropy, nonbug lines: " + '{0:.4f}'.format( avgnent))

# DR. RAY'S INFORMATION
for row in csv_r:
    if i == 0:
        i = 1
    else:
        if snapshot == 1:
            newpath = str(row[1] + "__" + row[3])
        elif snapshot == 0:
            newpath = str(row[3])
        newpath = newpath.replace("/","__")
        reflines.append([newpath,int(row[4])])
refdict = {}
for k, v in reflines:
    refdict.setdefault(k, set()).add(v)

tot = dict_size(refdict)

print("\n<< VERIFIED >>")
print("Number of buggy files found:   " + str(len(refdict)))
print("Number of verified bugs:       " + str(tot))

# PMD INFORMATION
for row in csv_p:
    if i == 1:
        i = 2
    else:
        newpath = str(row[2])
        newpath = newpath.replace("nonChange/","")
        newpath = newpath.replace("/","__")
        if snapshot == 0:
            newpath = newpath.split("__",1)[1]
            newpath = newpath.split("__",1)[1]
        pmdlines.append([newpath,int(row[4])])
        typelines.append([ str(row[7]) , str(newpath + "+" + row[4]) ])
        if int(row[3]) == 1:
            hipri.append(str(row[7]))

pmddict = {}
for k, v in pmdlines:
    pmddict.setdefault(k, set()).add(v)
typedict = {}
for k, v in typelines:
    typedict.setdefault(k, set()).add(v)

pmd = dict_size(pmddict)

print("\n<< PMD >>")
print("Number of files in violation:  " + str(len(pmddict)))
print("Number of violations found:    " + str(pmd))
print("Types of violations reported:  " + str(len(typedict)))

# SETUP
found = 0
match = {}
epmatch = {}
nepmatch = {}
ebmatch = {}
nebmatch = {}
allmatch = {}
nallmatch = {}
f = open(out,"w")
f.write("File,Line\n")

end1 = time.time()

# SEARCHING ########################################################################
start = time.time()

# pmd vs bugs
found, match = dict_cmp(refdict,pmddict,int(spread))

# bugs vs entropy (buggy and nonbuggy)
ebfound, ebmatch = entropy_dict_match(refdict,ebuglines,int(spread))
nebfound, nebmatch = entropy_dict_match(refdict,elines,int(spread))
m = len(ebmatch)
n = len(nebmatch)
sum = 0
for i in ebmatch: sum += i[2]
if m == 0: m = 1
avgebmatch = sum/m
sum = 0
for i in nebmatch: sum += i[2]
if n == 0: n = 1
navgebmatch = sum/n

# pmd vs entropy (buggy and nonbuggy)
epfound, epmatch = entropy_dict_match(pmddict,ebuglines,int(spread))                
nepfound, nepmatch = entropy_dict_match(pmddict,elines,int(spread))
m = len(epmatch)
n = len(nepmatch)
sum = 0
for i in epmatch: sum += i[2]
if m == 0: m = 1
avgematch = sum/m
sum = 0
for i in nepmatch: sum += i[2]
if n == 0: n = 1
navgematch = sum/n

# holistic matching
allfound, allmatch = entropy_l_match(match,ebuglines,int(spread))
nallfound, nallmatch = entropy_l_match(match,elines,int(spread))
m = len(allmatch)
n = len(nallmatch)
sum = 0
for i in allmatch: sum += i[2]
if m == 0: m = 1
avgallmatch = sum/m
sum = 0
for i in nallmatch: sum += i[2]
if n == 0: n = 1
navgallmatch = sum/n

# pmd type-matching
typeout, numbad, comm = pmd_type_match(typedict, hipri, match)

#allmatch: file, line, entropy for 3-way matches (find violations)
allmatchviolation = []
nallmatchviolation = []
for i in allmatch:
    for k in typedict:
        for v in typedict[k]:
            a = v.split("+")[0]
            b = v.split("+")[1]
            if a == i[0] and int(b) == int(i[1]):
                allmatchviolation.append([a,b,str(k)])

for i in nallmatch:
    for k in typedict:
        for v in typedict[k]:
            a = v.split("+")[0]
            b = v.split("+")[1]
            if a == i[0] and int(b) == int(i[1]):
                nallmatchviolation.append([a,b,str(k)])


end = time.time()
###################################################################################

# WRITE OUT
for line in match:
    f.write(str(line[0])+","+str(line[1])+"\n")

# CLEANUP
p.close()
r.close()
e.close()
f.close()
if tot == 0:
    tot = 1

# TEST INFORMATION
print("\n<< DATA >>")
print("Preprocessing time:            " + '{0:.4f}'.format(end1 - start1) + "s")
print("Search time:                   " + '{0:.4f}'.format(end - start) + "s")
print("Search radius:                 " + str( int(spread) * 2 ))
print("Shared by PMD and Entropy:     " + str(epfound))
print("Shared by PMD and Bug Data:    " + str(found))
print("Shared by Bug Data and Entropy:" + str(ebfound))
print("Shared by all three methods:   " + str(allfound))

print("\nBUG DATA vs PMD")
print("Number of matched lines:       " + str(found))
print("True match percentage:         " + '{0:.4f}'.format(found/tot * 100) + "%")
print("Verified bugs w/o violation:   " + str(tot-found))
print("PMD violations without match:  " + str(pmd-found))
print("# of critical violations:      " + str(numbad))
print("Most common rule violations:   ")
for i in comm:
    print('{0:<40} {1:<6}'.format(i[0],str(i[1])))

print("\nENTROPY DATA vs PMD")
print("Number of matched buggy lines: " + str(epfound))
print("Number of matched nobug lines: " + str(nepfound-epfound))
print("Avg entropy of buggy matches:  " + '{0:.4f}'.format( avgematch))
print("Avg entropy of nobug matches:  " + '{0:.4f}'.format( navgematch))
print("True match percentage:         " + '{0:.4f}'.format( epfound/len(ebuglines)*100) + "%")
print("Verified bugs w/o violation:   " + str( len(ebuglines) - epfound))

print("\nENTROPY DATA vs BUG DATA")
print("Number of matched buggy lines: " + str(ebfound))
print("Number of matched nobug lines: " + str(nebfound-ebfound))
print("Avg entropy of buggy matches:  " + '{0:.4f}'.format( avgebmatch))
print("Avg entropy of nobug matches:  " + '{0:.4f}'.format( navgebmatch))
print("True match percentage:         " + '{0:.4f}'.format( ebfound/len(ebuglines)*100) + "%")
print("Entropy bugs w/o match:        " + str( len(ebuglines) - ebfound))

print("\nENTROPY DATA vs BUG DATA vs PMD")
print("Number of matched buggy lines: " + str(allfound))
print("Number of matched nobug lines: " + str(nallfound-allfound))
print("Avg entropy of buggy matches:  " + '{0:.4f}'.format( avgallmatch))
print("Avg entropy of nobug matches:  " + '{0:.4f}'.format( navgallmatch))
print("True match percentage:         " + '{0:.4f}'.format( allfound/len(ebuglines)*100) + "%")
print("Entropy bugs w/o match:        " + str( len(ebuglines) - allfound))
if len(allmatchviolation) > 0:
    print("Reported by all three:")
    for i in allmatchviolation:
        print('{0:<40} {1:<6} {2:<40}'.format(i[0],i[1],i[2]))

if len(nallmatchviolation) > 0:
    print("Reported by all three (entropy reports nonbuggy):")
    for i in nallmatchviolation:
        if i not in allmatchviolation:
            print('{0:<40} {1:<6} {2:<40}'.format(i[0],i[1],i[2]))
