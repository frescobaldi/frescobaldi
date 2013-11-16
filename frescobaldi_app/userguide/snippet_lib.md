=== Maintaining a library of snippets ===
    
To keep a certain group of snippets manageable as a snippet
library, you can of course prefix the snippet titles with some sort
of special name. But a smarter way is to use a snippet variable.

It is suggested to use the `{set}` variable, and set it to the name of the
library you want the snippet to belong to.

Then in the snippet manager, you can easily select all the snippets 
belonging to the library by entering `:{set} name` in the snippet search 
bar, where "`name`" is the name you want to use. And then e.g. export the 
snippets to an XML file for sharing the snippets with others.


#VARS
set text set
