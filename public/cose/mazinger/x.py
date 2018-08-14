import re

begin = []
end = []

for line in open('riassunti.txt'):
    begin.append(line[:40].strip())
    end.append(line[41:].strip())
print re.sub('(\d+\.)', r'\n\n\1', ' '.join(begin + end))
