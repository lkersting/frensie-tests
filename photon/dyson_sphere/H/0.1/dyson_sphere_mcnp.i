dyson sphere
1  0         -1  imp:p=1
2  0        -2  imp:p=1
3  0        -3  imp:p=1
4  0        -4  imp:p=1
5  0        -5  imp:p=1
6  0        -6  imp:p=1
7  0        -7  imp:p=1
8  0        -8  imp:p=1
9  0        -9  imp:p=1
10  0        -10  imp:p=1
11  0        -11  imp:p=1
12  0        -12  imp:p=1
13  0        -13  imp:p=1
14  1  -0.001  14 -15 -16  imp:p=1
15  0  -17 (-14:15:16) 1 2 3 4 5 6 7 8 9 10 11 12 13  imp:p=1
16  0         17  imp:p=0

1 tz 0 0 98.8771077936 14.9438132474 0.1 0.1
2 tz 0 0 96.5925826289 25.8819045103 0.1 0.1
3 tz 0 0 86.6025403784 50.0 0.1 0.1
4 tz 0 0 70.7106781187 70.7106781187 0.1 0.1
5 tz 0 0 50.0 86.6025403784 0.1 0.1
6 tz 0 0 25.8819045103 96.5925826289 0.1 0.1
7 tz 0 0 6.12323399574e-15 100.0 0.1 0.1
8 tz 0 0 -25.8819045103 96.5925826289 0.1 0.1
9 tz 0 0 -50.0 86.6025403784 0.1 0.1
10 tz 0 0 -70.7106781187 70.7106781187 0.1 0.1
11 tz 0 0 -86.6025403784 50.0 0.1 0.1
12 tz 0 0 -96.5925826289 25.8819045103 0.1 0.1
13 tz 0 0 -98.8771077936 14.9438132474 0.1 0.1
14 pz -0.0005
15 pz  0.0005
16 cz  0.1
17 so  10000.0

mode p
nps   1e9
sdef  pos = 0 0 -0.1  dir = 1  vec = 0 0 1  erg = 0.1
c
m1    1000.12p 1.0
c
fcl:p 0 0 0 0 0 0 0 0 0 0 0 0 0 -1 0 0
f04:p 1 2 3 4 5 6 7 8 9 10 11 12 13
f14:p 1 2 3 4 5 6 7 8 9 10 11 12 13
e04 1e-3 998i 0.1
e14 1e-3 9980i 0.1
ft4 INC
fu4 0 1
phys:p 100 1 0 0 0
prdmp  j  1e7  1   1
