import os
import argparse as ap
import shutil as SH
import subprocess
import signal
import time
from subprocess import Popen, PIPE
from os import listdir
import os;
from os.path import isfile, join

class AutoGrade:
    def __init__(self):

        self.dir = ''; # Directory where everything lies
        self.main_dir = ''; # Directory where the main cpp file is contained
        self.input_dir = ''; # Directory where test cases is found

        self.time_limit = 60; # Time limit => default is 60 seconds

        self.pname = ''; # Program name to look for <pname.cpp>
        self.foutput = ''; # File generated from program => example: foutput = "p1.txt"

        self.case_senstivity = True; # True if you want to compare output case sensitively
        self.file_streams = False; # True if the program uses fstreams

        self.main_cout = []; # Output generated from the main program using Cout stream
        self.main_fout = []; # Output generated into a file

        self.input_data = [];

    # SETTERS FOR CLASS ATTRIBUTES
    def set_dir(self,dirc):
        self.dir = dirc;
        os.chdir('./' + dirc + '/');

    def set_main_dir(self,main_dir):
        self.main_dir = main_dir;

    def set_input_dir(self,idir):
        self.input_dir = idir;

    def set_time(self,limit):
        self.time_limit = limit;

    def set_pname(self,filename):
        self.pname = filename;

    def set_foutput(self,name):
        self.foutput = name;

    def set_case_sense(self,case):
        self.case_senstivity = case;

    def set_file_streams(self,flag):
        self.file_streams = flag;

    # GENERIC FUNCTION THAT EXECUTES A PROGRAM AND RETURNS THE STANDARD OUTPUT
    # AND ANY ERRORS IF FOUND
    def execute_program(self,input_data):

        errs = '';
        cenv = os.environ.copy();


        #Building the cpp file and checking for Compilation errors


        make_file = Popen(["make " + self.pname],shell=True,stderr=PIPE ,stdout = PIPE);
        make_file.wait();

        #IF MAKE FILE EXISTS THEN THE PROGRAM HAS COMPILED
        #OTHERWISE THERE MUST HAVE BEEN A COMPILATION ERRORS

        if(os.path.exists('./' + self.pname) == False):
            errs = '';
            while True:
                f = make_file.stderr.readline();
                if(f == ''):
                    break;
                else:
                    errs += f;

            return {'result':'cerr', 'errors': errs};



        try:
            p = Popen(['./'+self.pname], shell=True, stdout=PIPE, stdin=PIPE, stderr = PIPE, env=cenv);
        except Exception as e:
            #print e;
            print 'runtime error';



        #Passing Input to the program
        for ii in input_data:
            value = str(ii) + '\n'
            p.stdin.write(value)

        p.stdin.flush()

        #Checking whether the program has finished or not and killing it after time_limit
        start_time = time.time();
        while(p.poll() is None):

            if(time.time()-start_time >= self.time_limit):
                p.terminate();
                return {'result':'inf', 'errors': errs};


        #Gathering output
        result = "";
        x = p.stdout.readline().strip();
        while(x != ""):
            result = result + x;
            x = p.stdout.readline().strip();


        while True:
            x = p.stderr.readline();
            if(x == ''):
                break;
            else:
                errs += x;

        return {'result':result, 'errors': errs};
        # END OF EXECUTE PROGRAM


    def read_from_file(self,fname):

        try:
            with open(fname) as f:
                content = f.readlines();
                content = [x.strip() for x in content];
                return content;
        except Exception as e:
            print 'Error file Not Found \n\n';
            return False;



    def get_main_inputs(self):

        #finding all files in self.inputs_directory
        all_inputs = [];
        onlyfiles = [f for f in listdir('./'+self.input_dir+'/') if isfile(join('./'+self.input_dir+'/', f))];
        for fi in onlyfiles:
            if(fi != '.DS_Store'):
                all_inputs.append(self.read_from_file('./' + self.input_dir + '/' + fi));

        self.input_data = all_inputs;



    def run_main(self):

        os.chdir('./' + self.main_dir + '/');

        for test_case in self.input_data:

            main_output = self.execute_program(test_case);
            self.main_cout.append(main_output['result']);

            if(self.file_streams == True):
                fout_listed = self.read_from_file(self.foutput);
                if(len(fout_listed) != 0):
                    self.main_fout.append("\n".join(fout_listed));
                else:
                    self.main_fout.append(" ");
        os.chdir('../');

    def compare_results(self,student_cout,student_fout,student_dir,student_errors):

        err = '';
        i = 1;
        for error in student_errors:
            if(error.strip() != ''):
                err += "Test " + str(i) + "\n";
                err += error;
                err += "\n\n\n";
            i+=1;


        score = 0;
        results = '';

        output  = "Student Name: " + student_dir.replace('_' , ' ') + '\n';
        output += "----------------------------------------------\n";


        if(student_cout[0] == 'cerr'):
            output += "Compilation Error \n";
        else:
            for i in range(0,len(self.input_data)):

                results += "Test " + str(i+1) + "\n";
                results += "----------------------------------------------\n";
                # results += "----------------------------------------------\n";

                if (student_cout[i] == "inf"):
                    results += "Time Limit Exceeded, Please Check Again";
                else:
                    results += "Input: \n";
                    results += "\n".join(self.input_data[i]);
                    results += "\n----------------------------------------------\n";

                    results += "\nExpected Standard Output: \n";
                    results += self.main_cout[i] + "\n";
                    results += "----------------------------------------------\n";
                    results += "Actual Standard Output: \n";
                    results += student_cout[i]+ "\n";
                    results += "----------------------------------------------\n";

                    if(self.file_streams):
                        results += "\nExpected File Output: \n";
                        #print self.main_fout;
                        results += self.main_fout[i];
                        results += "\n";
                        results += "----------------------------------------------\n";
                        results += "Actual File Output: \n";
                        # print "I : " ;
                        # print i;
                        # print len(student_fout);
                        if(len(student_fout) > i):
                            results += student_fout[i];
                        results += "\n";
                        results += "----------------------------------------------\n";

                    results += "Verdict: ";


                    # COMPARING FILE STREAMS OUTPUT
                    check_fstreams = False;
                    if(self.file_streams == True):
                        if(self.case_senstivity == False):
                            if(len(student_fout) > i):
                                if(student_fout[i].lower() == self.main_fout[i].lower()):
                                    check_fstreams = True;
                        else:
                            if(len(student_fout) > i):
                                if(student_fout[i] == self.main_fout[i]):
                                    check_fstreams = True;
                    else:
                        check_fstreams = True;


                    # COMPARING STANDARD STREAMS OUTPUT
                    check_cout = False;
                    if(self.case_senstivity == False):
                        if(student_cout[i].lower() == self.main_cout[i].lower()):
                            check_cout = True;
                    else:
                        if(student_cout[i] == self.main_cout[i]):
                            check_cout = True;

                    # PRINTING THE VERDICT
                    if(check_cout == True and check_fstreams == True):
                        score+=1;
                        results+="OKAY";
                    else:
                        results+="Wrong Answer";


                results += "\n\n\n";

        output+= "Score: " + str(score) + "/" + str(len(self.input_data)) + '\n\n';
        output+= results;

        return {'output':output , 'errors':err};

    def push_results(self,student_results):

        target = open("results.txt",'w');
        target.truncate();
        target.write(student_results['output']);
        target.close();

        if(student_results['errors'].strip() != ''):
            target = open("erros.txt",'w');
            target.truncate();
            target.write(student_results['errors']);
            target.close();



    def run_tests(self):


        for student_dir in os.listdir('.'):
            if(student_dir != '.DS_Store' and student_dir != self.main_dir and student_dir != self.input_dir):

                os.chdir('./' + student_dir + '/');
                student_cout = [];
                student_fout = [];
                student_errors = [];

                for test_case in self.input_data:

                    current_output = self.execute_program(test_case);

                    student_cout.append(current_output['result']);
                    if(self.file_streams == True):
                        fout_listed = self.read_from_file(self.foutput);
                        if(fout_listed != False):
                            if(len(fout_listed) != 0):
                                student_fout.append("\n".join(fout_listed));
                            else:
                                student_fout.append(" ");


                    student_errors.append(current_output['errors']);

                student_results = self.compare_results(student_cout,student_fout,student_dir,student_errors);
                self.push_results(student_results);
                os.chdir('../');


# ACTUAL CODE BELOW

autograder = AutoGrade();
autograder.set_dir('A4P1');
autograder.set_main_dir('0_main');
autograder.set_input_dir('1_inputs');
autograder.set_time(5);
autograder.set_pname('xo');
autograder.set_foutput('file.txt');
autograder.set_case_sense(False);
autograder.set_file_streams(True);


autograder.get_main_inputs();
autograder.run_main();
autograder.run_tests();
