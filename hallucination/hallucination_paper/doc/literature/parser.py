import os 
import re

def merge():
    path = os.getcwd()

    lines = []

    files = os.listdir(path)
    for file in files:
        if not file.endswith('.csv'):
            continue
        if 'google' in file:
            continue
        firstLine = True
        print(file)
        with open(file, 'r') as f:
            for line in f:
                if firstLine:
                    firstLine = False
                    continue
                lines.append(line.strip('\n'))
    with open('scopus_semantic_crossref_no_google.csv','w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')
# merge()



# with open('scopus_semantic_crossref_no_google.csv','r') as f:
#     dic = set()
#     lines2 = []
#     pat = re.compile('\"(.*?)\"')
#     cnt = 0
#     for line in f:
#         data = pat.findall(line)
#         cnt +=1 
#         print(data[1])
#         print(cnt)
#         if cnt ==100:
#             break
#         if data[1] in dic:
#             continue
#         else:
#             dic.add(data[1])
#             lines2.append(line)
# with open('scopus_semantic_crossref_no_google_remove_duplicate.csv','w') as f:
#     for line in lines2:
#         f.write(line)
# print(len(lines2))


def togooglecsv():
    f2 = open('google_merge.csv','w')
    flag = True
    with open('google_merge.txt','r') as f:
        for line in f:
            line = line.strip('\n')
            if flag:
                f2.write('\"')
                f2.write(line)
                f2.write('\"')
                f2.write(',')
                flag = False
                continue
            else:
                f2.write('\"')
                f2.write(line)
                f2.write('\"')
                f2.write('\n')
                flag = True
                continue
    f2.close()
togooglecsv()