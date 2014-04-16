GoGramming
==========

4th Year Project Application



Application Structure

The main implementation of the application consists of numerous template files; a "views.py" file; 
a "models.py" file; and a "forms.py" file. The template files contain the details of the application 
web pages. The "views.py" file contains the Python back-end code. The "models.py" file contains the 
details of the database structure. The "forms.py" file contains the details of the web forms in the 
application. Additionally several JavaScript and CSS files are utilised.



System Administrator Guide


Installing the application:

1.	Setup a “Raspberry Pi” with the “Raspbian” operating system installed.
2.	Download the “GoGramming” application from the “GitHub” project repository. This can be accessed through this URL: https://github.com/MadAd360/GoGramming 
3.	Install “Nginx” through the “apt-get” Linux command.
4.	Install “Git” through the “apt-get” Linux command.
5.	Install “PostgreSQL” through the “apt-get” Linux command.
6.	Create “PostgreSQL” database through the “createdb” Linux command.
7.	Change directory paths and other variables in the “config”, “settings”, “gogramming_nginx” and “gogramming_uwsgi” files appropriately. 
8.	Copy the “gogramming_nginx.conf” file into the “/etc/nginx/sites-enabled/” folder.
9.	Restart “Nginx”.
10.	Run “uWSGI” through the below Linux command:
		sudo uwsgi --ini /home/pi/application/gocompile/flask/gocompile_uwsgi.ini & 
11.	To automatically start server on reboot add the Linux command above through the Linux “crontab” command.

Adding new languages:

1.	Add the necessary files to compile and run the language in the “plugin-resources” folder.
2.	Create a new Python file in the “plugins” folder.
3.	Create a new Python class which inherits from the “Language” class.
4.	Implement the stated functionality in this class.
5.	Run the “language_loader” Python program.



User Guide


The below steps highlight the process of accessing the application and running a program.

1.	Access “GoGramming” application through the following URL: http://www.gogramming.co.uk/ 
2.	Create an account by selecting the “Create Account” and entering the appropriate information. This must then be activated through email confirmation.
3.	Enter the details of the created account into the login page to access other features of the application.  
4.	Create a new file with the appropriate name and file type through the “Create” dropdown menu on the navigation bar.
5.	Select the “Edit” button relating to the created file and alter its content through the editor. Save these changes by selecting the “Save” button. If the language is interpreted then jump to step 7.
6.	Select the “Compile” button. If an issue has occurred with the compilation an error message will be displayed. The exact compilation error will also be displayed to allow for debugging. If an error exists then return to step 5.
7.	Select the “Run” button. An interactive page will open allow the program to be interacted with. If any error are displayed in the output of the program then return to step 5 to resolve these issues.


