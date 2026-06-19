k = 0
kA = 0
m = 10000
c = ''

s = open('24_28943.txt').readline()

for c in 'EIOUY':
    s = s.replace(c, 'A')

for r in range(len(s)):
    if r % 500000 == 0:
        print(r, len(s))

    c += s[r]

    if c[-2:] == '20':
        k += 1

    if c[-1] == 'A':
        kA += 1

    while k >= 26 or kA >= 1:
        if c[:2] == '20':
            k -= 1

        if c[0] == 'A':
            kA -= 1

        c = c[1:]
        if kA == 1 and k == 26:
            m = min(m, len(c))
print(m)