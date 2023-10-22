# PUME
PUME (Python Universal Mutation Engine) is a program that mutates the source code of python files making modifications 
to the abstract syntax tree.

The performed modifications are:
- Change the names of classes, functions, local variables and global variables.
- Change the position of the functions.
- Adds the reserved word pass randomly in the code.
- Adds random comments in the code.
- Replaces integers with a mathematical expression which has the same value.
- Replaces strings with an addition of strings which has the same value.

## Usage
```
usage: main.py [-h] File(s) [File(s) ...]

Mutates the code of python files

positional arguments:
  File(s)     File(s) to be mutated

options:
  -h, --help  show this help message and exit
```

### Examples
Mutating the following file:
```python
def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

apples_john = 42
apples_martha = 94
total_apples = apples_john + apples_martha
print(total_apples)
```

With the command:
```commandline
python3 main.py test.py
```

The result will be something like:
```python
pass
#hQKsEGNsBUttyGaLxKdrjUqSbAyNuvGRBDFv
#UcHxoCVmpadCJjEMOGXE
#OVMdgDxdasBAPyob

   #KjPIE
                 #NhnshiAlGQWatgWvBXCvwDX
def yRISfJJLFYcCB(IfzTnvJzzOfD, oozoSrKlAUurkRl):
    #IUrLqBdFastoeszONgkJgIeAzsiTeXEb
    #nWpQkcBE
   #zQAfNsOdjDsLqYnsLziVW
    pass
    pass
    pass
   #eiM
    pass
    pass
    return IfzTnvJzzOfD + oozoSrKlAUurkRl
 #LHvZKXoZO
pass
pass
pass

             #voOWLvKxPlksktguZvuzQbIywgGxESaniOpHLHsYzfGnm
def bYaDYqOSvs(mCBYoSvNPRirG, AaJqZPs):
      #QECoOMLgPErZOUfRWJgkqjTnzswUkmfixUwIqLUVOlHqK
   #kLX
      #TdweIadSTrqrGq
    return mCBYoSvNPRirG * AaJqZPs
#oK

 #fivPmMMNE
def hVTOYKoPTiq(RvTTzGE, gmxSr):
           #lMJtggAwRugfZfYRRaifRmo
    return RvTTzGE - gmxSr
                          #isWGSrZu
 #YrjR
ldcMlNGbCNzJF = 808 + 312 % 105 // 509 // 516 // 252 // 943 - 766
  #kc
pass
                      #ArpogaFTwl
DkvElJg = 361 // 648 // 449 + 482 // 543 - 928 % 270 * 666 + 828 + 77854
    #mohYOSFRtVrGCOr
aRaEKqjlQFPEGvp = yRISfJJLFYcCB(ldcMlNGbCNzJF, DkvElJg)
     #mdb
       #jxGyBvFRAbqRbfUeasMAcQnlFKP
print(aRaEKqjlQFPEGvp)
```

To mutate two files you can use the following command:
```commandline
python3 main.py file_1.py file_2.py
```

The program also works with a lot of files in different directories:
```commandline
python3 main.py whoissearch.py whoissearch/*.py whoissearch/classifiers/*.py whoissearch/data/*.py whoissearch/parsers/*.py
```

### Output
The mutated files will be stored in a new directory called __results__. The files and folders created inside the 
results directory will have the same name as the original ones.

## Limitations
- [Due to the way real numbers are handled in Python](https://docs.python.org/3/tutorial/floatingpoint.html#floating-point-arithmetic-issues-and-limitations), they will not be mutated.
In the following image you can see the type of errors that can happen:
![A python's error handing floats](./images/float_problem.png)
- Due to typing in Python is dynamic, you cannot figure out what type variable the programmer is using until the 
program is running. So when PUME is changing names of functions and two classes which have the same name for a 
function, it does not know which function belongs to which class. __So the programmer cannot create two functions with 
the same name in different classes. This also applies to the standard libraries.__
In the following example, the programmer is creating a class with a function that shares name with other function of 
the standard library. In this situation, PUME cannot differentiate which function is calling.
```python
class MyClass:
    def __init__(self):
        self.data = ["a", "b", "c", "d"]
    def find(self, a):
        return self.data.index(a)

my_string = "The car is big"
my_string = my_string.find("car")
my_class = MyClass()
position = my_class.find("a")
```

In order to avoid a bug in the mutated program, the programmer has to change the name of the class function that he 
created:
```python
class MyClass:
    def __init__(self):
        self.data = ["a", "b", "c", "d"]
    def search(self, a):
        return self.data.index(a)

my_string = "The car is big"
my_string = my_string.find("car")
my_class = MyClass()
position = my_class.search("a")
```

## Additional info
In [this post](https://hackliza.gal/en/posts/pume/) I explain more in detail what the program does. The post is in 
[galician](https://hackliza.gal/posts/pume/) too.
