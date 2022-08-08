# Deserek
Python code to Serialize and Unserialize java binary serialization format. 

For reading/writing uses https://github.com/k3idii/bytewirez

This code prints A LOT of debug message (for now).
It makes understanding the format easier. 

And you can alway do ` 2>/dev/null`...

# Usage:
` python deserek.py binar-or-base64-file [options] `

### The obvious: deserializaton :
```
# python deserek.py examples/ysoserial_url/payload_url.txt  --out [format]

```
Where format :
* json == json
* yaml == yaml (from json)
* python == output valid python code

Example:
```
# python deserek.py examples/ysoserial_url/payload_url.txt  --out python > tmp.py

# python tmp.py 2>/dev/null | xxd
00000000: aced 0005 7372 0011 6a61 7661 2e75 7469  ....sr..java.uti
00000010: 6c2e 4861 7368 4d61 7005 07da c1c3 1660  l.HashMap......`
00000020: d103 0002 4600 0a6c 6f61 6446 6163 746f  ....F..loadFacto
00000030: 7249 0009 7468 7265 7368 6f6c 6478 703f  rI..thresholdxp?
00000040: 4000 0000 0000 0c77 0800 0000 1000 0000  @......w........
00000050: 0173 7200 0c6a 6176 612e 6e65 742e 5552  .sr..java.net.UR
00000060: 4c96 2537 361a fce4 7203 0007 4900 0868  L.%76...r...I..h
00000070: 6173 6843 6f64 6549 0004 706f 7274 4c00  ashCodeI..portL.
00000080: 0961 7574 686f 7269 7479 7400 124c 6a61  .authorityt..Lja
00000090: 7661 2f6c 616e 672f 5374 7269 6e67 3b4c  va/lang/String;L
000000a0: 0004 6669 6c65 7100 7e00 034c 0004 686f  ..fileq.~..L..ho
000000b0: 7374 7100 7e00 034c 0008 7072 6f74 6f63  stq.~..L..protoc
000000c0: 6f6c 7100 7e00 034c 0003 7265 6671 007e  olq.~..L..refq.~
000000d0: 0003 7870 ffff ffff ffff ffff 7400 1074  ..xp........t..t
000000e0: 6573 742e 6578 616d 706c 652e 636f 6d74  est.example.comt
000000f0: 0001 2f71 007e 0005 7400 0468 7474 7070  ../q.~..t..httpp
00000100: 7874 0018 6874 7470 3a2f 2f74 6573 742e  xt..http://test.
00000110: 6578 616d 706c 652e 636f 6d2f 78         example.com/x

# python tmp.py > test.bin
#java -cp jv DeSerial test.bin 
Working on it ... 
{http://test.example.com/=http://test.example.com/}


```


### test stability :
This mode test if serialization and deserialization is "stable" - if the binary output of serialization of unserialized data is same :)

```
# python deserek.py examples/ysoserial_url/payload_url.txt  --test
  (...)
UNSERILIZED !
  (...)
Testing serialization : 
  (...)
SERIALIZED :  LEN1=285 , LEN2=285 
  (...)
TEST serialization from python code ...
  (...)
SERIALIZED :  LEN1=285 , LEN2=285 

If you see this message means that (de)serializator is stable !

```
