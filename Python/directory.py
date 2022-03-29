class Person(object):
    def __init__(self, name, email):
        self.name = name
        self.email = email
    def print_directoryP(self):
        print(self.name)
        print(self.email)

class Student(Person):
    def __init__(self, name, email, major, classlevel):
        super(Student, self).__init__(name, email)
        self.major = major
        self.classlevel = classlevel
    def print_directoryP(self):
        super()
        print(self.name)
        print(self.email)
        print(self.major) 
        print(self.classlevel)  

class Employee(Person):
    def __init__(self,name, email,department,office_location):
        super(Employee,self).__init__(name, email)
        self.department = department
        self.office_location = office_location
    def print_directoryP(self):
        super()
        print(self.name)
        print(self.email)
        print(self.department) 
        print(self.office_location)

class Faculty(Person):
    def __init__(self,name, email,department,office_location,research_area):
        super(Faculty,self).__init__(name, email)
        self.research_area = research_area
        self.office_location = office_location
    def print_directoryP(self):
        super()
        print(self.name)
        print(self.email)
        print(self.office_location)
        print(self.research_area)

p1 = Person("John Doe","jdoe@ilstu.edu\n")
p2 = Person("Samson","Sokunol@ilstu.edu\n")

s1 = Student("John Doe","jdoe@ilstu.edu","Political Science","Junior\n")
s2 = Student("Samson Okunola","Sokunol@ilstu.edu","Computer Science","Junior\n")

e1 = Employee("John Doe","jdoe@ilstu.edu", "English", "STV 404B\n")  
e2 = Employee("Samson","Sokunol@ilstu.edu", "IT", "jullian hall\n")  

f1 = Faculty("Mary Elaine Califf","mecalif@ilstu.edu","Information Technology","WIH 17A","Machine Learning, Natural Language Processing, CS Education\n")
f2 = Faculty("Samson Okunola","Sokunol@ilstu.edu","Information Technology","WIH 17A","Machine Learning, Natural Language Processing, CS Education\n")

list=[p1,p2,s1,s2,e1,e2,f1,f2]
for obj in list:
   obj.print_directoryP()








