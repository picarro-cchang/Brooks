<?xml version="1.0" encoding="utf-8"?>
<!-- Created by Leo: http://leoeditor.com/leo_toc.html -->
<?xml-stylesheet ekr_test ?>
<leo_file xmlns:leo="http://leoeditor.com/namespaces/leo-python-editor/1.1" >
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.5" body_secondary_ratio="0.5">
	<global_window_position top="50" left="50" height="500" width="700"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="sze.20151110000149.1" a="E"><vh>Documentation (make-sphinx here)</vh>
<v t="sze.20151110001245.1"><vh>@edit sphinx/conf.py</vh></v>
<v t="sze.20151110000629.1"><vh>@edit sphinx/index.html.txt</vh></v>
<v t="sze.20151110000823.1" a="E"><vh>@rst sphinx/pipelines.html</vh>
<v t="sze.20151110001008.1"><vh>Introduction</vh></v>
</v>
</v>
<v t="sze.20151109235025.1"><vh>Startup</vh>
<v t="sze.20151109235025.2"><vh>@button make-sphinx</vh></v>
<v t="sze.20151109235025.3"><vh>@settings</vh>
<v t="sze.20151109235025.4"><vh>@string target_language = rest</vh></v>
<v t="sze.20151109235025.5"><vh>For rst3 command</vh>
<v t="sze.20151109235025.6"><vh>@bool rst3_call_docutils = False</vh></v>
<v t="sze.20151109235025.7"><vh>@bool rst3_write_intermediate_file = True</vh></v>
<v t="sze.20151109235025.8"><vh>@string rst3_write_intermediate_extension = .txt</vh></v>
</v>
</v>
</v>
<v t="sze.20151109235037.1"><vh>Leo's cheat sheet</vh>
<v t="sze.20151109235037.2"><vh>Key bindings</vh>
<v t="sze.20151109235037.3"><vh>Selecting outline nodes</vh></v>
<v t="sze.20151109235037.4"><vh>Moving outline nodes</vh></v>
<v t="sze.20151109235037.5"><vh>Moving the cursor</vh></v>
</v>
<v t="sze.20151109235037.6"><vh>Frequently used commands</vh></v>
<v t="sze.20151109235037.7"><vh>Leo directives</vh></v>
<v t="sze.20151109235037.8"><vh>Settings</vh></v>
<v t="sze.20151109235037.9"><vh>Node types</vh></v>
<v t="sze.20151109235037.10"><vh>Notable Plugins</vh></v>
<v t="sze.20151109235037.11"><vh>External files (@&lt;file&gt; nodes)</vh></v>
<v t="sze.20151109235037.12"><vh>Scripting</vh>
<v t="sze.20151109235037.13"><vh>Pre-defined symbols</vh></v>
<v t="sze.20151109235037.14"><vh>Generators</vh></v>
<v t="sze.20151109235037.15"><vh>Commands class</vh></v>
<v t="sze.20151109235037.16"><vh>vnode class</vh></v>
<v t="sze.20151109235037.17"><vh>position class</vh></v>
<v t="sze.20151109235037.18"><vh>leo.core.leoGlobals module</vh></v>
</v>
</v>
</vnodes>
<tnodes>
<t tx="sze.20151109235025.1">By convention, a Startup node contains settings, scripts, etc.
that mostly one wants to have hidden.
</t>
<t tx="sze.20151109235025.2">@language python
import os

aList = c.rstCommands.rst3()
g.es(aList[0].h.strip())

import os
trace = True
g.cls()
c.setComplexCommand('make-sphinx')
c.save()
if aList:
    path = g.os_path_finalize_join(os.path.abspath(os.curdir),'sphinx')
    os.chdir(path)
    g.es('About to execute make clean and make html')
    g.execute_shell_commands('make clean',trace=trace)
    g.execute_shell_commands('make html',trace=trace)
</t>
<t tx="sze.20151109235025.3">**Imortant**: to take effect, all settings must be descendants of this
@settings node.

**Note**: This file colors text as reStructuredText by default because of
the setting::

    @string target_language = rest
</t>
<t tx="sze.20151109235025.4">The default language if no @language or @comment is in effect.

Valid values are (case is ignored):

actionscript,c,csharp,css,cweb,elisp,html,java,latex,
pascal,perl,perlpod,php,plain,plsql,python,rapidq,rebol,shell,tcltk.</t>
<t tx="sze.20151109235025.5"></t>
<t tx="sze.20151109235025.6"># Use False when using Sphinx</t>
<t tx="sze.20151109235025.7"></t>
<t tx="sze.20151109235025.8"></t>
<t tx="sze.20151109235037.1"></t>
<t tx="sze.20151109235037.10">See the docstring of these plugins for more details:

- bookmarks.py: Manages URL's used as bookmarks.
- contextmenu.py: Brings up context menu when user right-clicks a headline.
- mod_scripting.py: Supports @button and @command nodes.
- quicksearch.py: Adds Nav tab for searching.
- todo.py: Manages to-do lists and simple project management.
- valuespace.py: Creates an outline-oriented spreadsheet.
- viewrendered.py: Creates a rendering pane. Automatically loaded by Leo's help commands.
</t>
<t tx="sze.20151109235037.11">\@&lt;file&gt; nodes create external files::

    @asis &lt;filename&gt;    
    @auto &lt;filename&gt;    
    @edit &lt;filename&gt;
    @file &lt;filename&gt;
    @nosent &lt;filename&gt;  
    @shadow &lt;filename&gt;
    
For full details, see Leo's Directives reference: http://leoeditor.com/directives.html
    
**Section names** have the form::

    &lt;&lt; any text, except double closing angle brackets &gt;&gt;
    
**Section-definition nodes** have headlines starting with a section name.

Leo performs **expansions** for all @&lt;file&gt; nodes except @asis.

Expansion of @all:

- Leo replaces @all by the *unexpanded* body text of *all* nodes.

Expansion of section names and @others:

- Leo replaces section names in body text by the *expanded*
  text of the corresponding section definition node.
  
- Leo replaces @others with the *expanded* text of all nodes
  that *aren't* section-definition nodes.
</t>
<t tx="sze.20151109235037.12">This section lists the ivars, properties, functions and methods most
commonly used in Leo scripts.

**Very important**: use Alt-1 (toggle-autocompleter) and Alt-2
(toggle-calltips) to recreate these lists as you type.

As an alternative to this chapter, Jacob Peck has written a more informal scripting tutorial:
http://blog.suspended-chord.info/2014/01/28/intro-to-leo-scripting/</t>
<t tx="sze.20151109235037.13">execute-script predefines::

    c: The commander of the present outline.
    g: The leo.core.leoGlobals module.
    p: The presently selected position, c.p.
    
@test scripts predefine all the above, plus::

    self: The instance of unittest.TestCase
</t>
<t tx="sze.20151109235037.14">::

    c.all_positions()
    c.all_unique_positions()
    p.children()
    p.parents()
    p.self_and_parents()
    p.self_and_siblings()
    p.following_siblings()
    p.subtree()
    p.self_and_subtree()
</t>
<t tx="sze.20151109235037.15">::

    c.frame         c's outer frame, a leoFrame instance.
    c.user_dict     a temporary dict for use of scripts and plugins.
    c.redraw()
    c.positionExists(p)

Here is a partial list of the **official ivars** of any leoFrame f::

    f.c                     is the frame’s commander.
    f.body                  is a leoBody instance.
    f.body.bodyCtl          is a leoQTextEditWidget instance.
    f.body.bodyCtrl.widget  is a LeoQTextBrowser(QTextBrowser) instance.
    f.log                   is a leoLog instance.
    f.tree                  is a leoQtTree instance.
    f.tree.treeWidget       is a LeoQTreeWidget (a QTreeWidget) instance.
    
Use autocompletion to explore these objects!
</t>
<t tx="sze.20151109235037.16">::

    v.b: v's body text.
    v.h: v's headline text.
    v.u: v.unknownAttributes, a persistent Python dictionary.
    
v.u (uA's or unknownAttributes or userAttributes) allow plugins or scripts
to associate persistant data with vnodes. For details see:
http://leoeditor.com/customizing.html#adding-extensible-attributes-to-nodes-and-leo-files
</t>
<t tx="sze.20151109235037.17">**Properties**::

    p.b: same as p.v.b.
    p.h: same as p.v.h.
    p.u: same as p.v.u.

**Getters**::

    p.back()
    p.children()
    p.firstChild()
    p.hasBack()
    p.hasChildren()
    p.hasNext()
    p.hasParent()
    p.hasThreadBack()
    p.hasThreadNext()
    p.isAncestorOf(p2)
    p.isAnyAtFileNode()
    p.isAt...Node()
    p.isCloned()
    p.isDirty()
    p.isExpanded()
    p.isMarked()
    p.isRoot()
    p.isVisible()
    p.lastChild()
    p.level()
    p.next()
    p.nodeAfterTree()
    p.nthChild()
    p.numberOfChildren()
    p.parent()
    p.parents()
    p.threadBack()
    p.threadNext()
    p.visBack()
    p.visNext()
    
**Setters**::

    p.setDirty()
    p.setMarked()

**Operations on nodes**::

    p.clone()
    p.contract()
    p.doDelete(new_position)
    p.expand()
    p.insertAfter()
    p.insertAsNthChild(n)
    p.insertBefore()
    p.moveAfter(p2)
    p.moveToNthChildOf(parent,n)
    p.moveToRoot(oldRoot=None)
        # oldRoot **must** be the old root position if it exists.
        
**Moving positions**

The following move positions *themselves*: they change the node to which a
position refers. They do *not* change outline structure in any way! Use
these when generators are not flexible enough::

    p.moveAfter(p2)
    p.moveToBack()
    p.moveToFirstChild()
    p.moveToFirstChildOf(p2)
    p.moveToLastChild()
    p.moveToLastChildOf(p2)
    p.moveToLastNode()
    p.moveToNext()
    p.moveToNodeAfterTree(p2)
    p.moveToNthChild()
    p.moveToNthChildOf(p2)
    p.moveToParent()
    p.moveToRoot()
    p.moveToThreadBack()
    p.moveToThreadNext()
    p.moveToVisBack(c)
    p.moveToVisNext(c)
</t>
<t tx="sze.20151109235037.18">For full details, see @file leoGlobals.py in LeoPyRef.leo.

**g vars**::

    g.app
    g.app.gui
    g.app.windowlist
    g.unitTesting
    g.user_dict  # a temporary dict for use of scripts and plugins.
    
**g decorator**::

    @g.command(command-name)
    
**g functions** (the most interesting: there are many more in leoGlobals.py)::
    
    g.angleBrackets()
    g.app.commanders()
    g.app.gui.guiName()
    g.es(*args,**keys)
    g.es_print(*args,**keys)
    g.es_exception()
    g.getScript(c,p,
        useSelectedText=True,
        forcePythonSentinels=True,
        useSentinels=True)
    g.openWithFileName(fileName,old_c=None,gui=None)
    g.os_path_... # Wrappers for os.path methods.
    g.pdb(message='')
    g.toEncodedString(s,encoding='utf-8',reportErrors=False)
    g.toUnicode(s, encoding='utf-8',reportErrors=False)
    g.trace(*args,**keys)
    g.warning(*args,**keys)
</t>
<t tx="sze.20151109235037.2"></t>
<t tx="sze.20151109235037.3">When focus is in the outline pane::

    Right-arrow (expand-and-go-right)
    Left-arrow (contract-or-go-left)
    Up-arrow (goto-prev-visible) 
    Down-arrow (goto-next-visible)
    
Regardless of focus::

    Alt-Home (goto-first-visible-node) 
    Alt-End (goto-last-visible-node)
    Alt-Right-arrow (expand-and-go-right)
    Alt-Left-arrow (contract-or-go-left)
    Alt-Up-arrow (goto-prev-visible) 
    Alt-Down-arrow (goto-next-visible)
</t>
<t tx="sze.20151109235037.4">When focus is in the outline::

    Shift-Down-arrow (move-outline-down) 
    Shift-Left-arrow (move-outline-left) 
    Shift-Right-arrow (move-outline-right) 
    Shift-Up-arrow (move-outline-up)

Regardless of focus::

    Alt-Shift-Down-arrow (move-outline-down) 
    Alt-Shift-Left-arrow (move-outline-left) 
    Alt-Shift-Right-arrow (move-outline-right) 
    Alt-Shift-Up-arrow (move-outline-up)
    Ctrl-D (move-outline-down)
    Ctrl-L (move-outline-left) 
    Ctrl-R (move-outline-right)
    Ctrl-U (move-outline-up)
</t>
<t tx="sze.20151109235037.5">When focus is in any of Leo's text panes (body pane, log pane, headlines):

    +-------------------+-----------------------+
    | **Key**           | **Move Cursor**       |
    +-------------------+-----------------------+
    | Arrow keys        | one character         |
    +-------------------+-----------------------+
    | Ctrl-LeftArrow    | back one word         |
    +-------------------+-----------------------+
    | Ctrl-RightArrow   | forward one word      |
    +-------------------+-----------------------+
    | Home              | beginning of line     |
    +-------------------+-----------------------+
    | End               | end of line           |
    +-------------------+-----------------------+
    | Ctrl-Home         | beginning of the body |
    +-------------------+-----------------------+
    | Ctrl-End          | end of body           |
    +-------------------+-----------------------+
    | PageDown          | down one page         |
    +-------------------+-----------------------+
    | PageUp            | up one page           |
    +-------------------+-----------------------+
    
Adding the Shift key modifier to any of the keys above
moves the cursor and extends the selected text.
</t>
<t tx="sze.20151109235037.6">For much more information, see Leo's Commands Reference: http://leoeditor.com/commands.html

Copy/Paste (text)::

    Ctrl-C (copy-text)
    Ctrl-K (kill)
    Ctrl-V (paste-text)
    Ctrl-X (cut-text)
    Ctrl-Y (yank)
    Alt-Y  (yank-pop)
    kill-...

Files::

    Ctrl-N (new) 
    Ctrl-O (open-outline)
    Ctrl-S (save-file) 
    Ctrl-Q (exit-leo)

Focus::

    Alt-T (focus-to-tree) 
    Ctrl-T (toggle-active-pane)
    Ctrl-Tab (tab-cycle-next)
    
Help::

    Alt-0 (vr-toggle)
    F1 (help) 
    F11 (help-for-command) 
    F12 (help-for-python)
    print-bindings
    print-settings
    help-for-...

Find/Replace::

    Ctrl-F (search-with-present-options) 
    Shift-Ctrl-R (replace-string)
    Ctrl-minus (replace-then-find) 
    F3 (find-next) 
    F2 (find-previous)
    
Minibuffer::

    Alt-X (full-command)
    Ctrl-G (keyboard-quit)

Nodes::

    Ctrl-I or Insert (insert-node)
    Ctrl-H (edit-headline)
    &lt;Return&gt; (when editing a headline) (end-edit-headline)
    Ctrl-Shift-C (copy-node)
    Ctrl-Shift-X (cut-node) 
    Ctrl-Shift-V (paste-node) 
    Ctrl-{ (promote)
    Ctrl-} (demote)
    Ctrl-M (mark) 

Undo::

    Ctrl-Z (undo)
    Ctrl-Shift-Z (redo)
</t>
<t tx="sze.20151109235037.7">Directives starting with '@ in the leftmost column
    
For full details, see Leo's Directives reference: http://leoeditor.com/directives.html

    @                       # starts doc part
    @c                      # ends doc part
    @color
    @doc                    # starts doc part
    @killcolor
    @nocolor
    @language python
    @language c
    @language rest          # restructured text
    @language plain         # plain text: no syntax coloring.
    @lineending lineending
    @pagewidth 100
    @raw, @end_raw          # @file only.
    @tabwidth -4            # use spaces
    @tabwidth 8             # use tabs
    @nowrap
    @wrap
    
Leading whitespace is allowed (and significant) for::

    @all
    @others
    </t>
<t tx="sze.20151109235037.8">For documentation see node: "About this file" in leoSettings.leo.

- Key bindings:     @shortcuts
- Visual settings:  @data qt-gui-plugin-style-sheet
- Enabling plugins: @enabled-plugins

To disable a binding for a key, bind it to do-nothing::

    do-nothing = Insert
    
This overrides the following default binding in leoSettings.leo::

    insert-node = Insert
</t>
<t tx="sze.20151109235037.9">Supported by Leo's core:

- @chapters, @chapter
- @rst, @rst-no-head, @rst-ignore, @rst-ignore-tree
- @settings
- @test, @testsetup, @testclass
- @url

Within @settings trees:

- @bool, @color, @directory, @encoding, @int
- @float, @font, @ratio, @path, @string
- @enabled-plugins
- @buttons, @commands
- @menus, @menu, @menuat, @item
- @openwith, @shortcuts

Supported by plugins:

- bookmarks.py: @bookmarks, @bookmark
- at_folder.py: @folder
- at_produce.py: @produce
- at_view.py: @clip, @strip, @view
- expfolder.py: @expfolder
- mod_scripting.py: @button, @command, @script
- viewrendered.py: @graphics-script, @image, @html, @md, @movie and @svg
- rss.py: @feed

</t>
<t tx="sze.20151110000149.1"></t>
<t tx="sze.20151110000823.1"></t>
<t tx="sze.20151110001008.1">This describes the implementation of a pipeline-based system for data processing based on a collection of interconnected blocks, each of which runs a task in a thread. The task is written as a loop which typically waits for some event, such as input becoming available, carries out some processing, and emits some output. A pipeline is made by defining a class which is a subclass of the ``Pipeline`` class. Minimally, the class must define the methods ``makeBlocks`` and ``linkBlocks``. Within ``makeBlocks``, the constructors of the blocks are invoked and assigned to attributes of the class. The method ``linkBlocks`` is then used to join up the blocks according to the desired topology of the pipeline.

In order to run the pipeline and wait for it to complete, it is necessary to instantiate the subclass, call its ``makeBlocks`` and ``linkBlocks`` methods and then its ``waitCompletion`` method. The waitCompletion method will reraise any exceptions from any blocks in the pipeline, even though the exceptions originate in a different thread. The waitCompletion method returns True when the pipeline is complete or False after the specified timeout, if the pipeline is still running. By using a timeout and looping as shown below, the application will respond to keyboard interrupts ::

    pipeline = PipeLineRealtime()
    pipeline.makeBlocks()
    pipeline.linkBlocks()
    while not pipeline.waitCompletion(0.5):
        pass

Tasks continue to run for the lifetime of the pipeline. 

The user creates blocks by defining a class and writing methods which describe the processing performed by instances of that block. 

The file ``Blocks.py`` contains definitions of the basic units. ``Block`` is the base class of the hierarchy. Associated with each block is a daemonic thread which, when started, runs the ``mainLoop`` method of the block. A block can have zero or more inputs and up to one output. The output of a block can be connected to inputs of other blocks. These inputs are called the *consumers* of the current block, and the ``linkTo`` method is used to register an input as a consumer. A block has a ``continuationFunc`` attribute which names a continuation function. This function is called when the ``mainLoop`` method returns. A block has a ``waitCompletion`` method which waits for the thread associated with the block to complete.

Each input of a block is an instance of the ``BlockInput`` class. Data are sent to an input as "messages", which are usually dictionaries. The ``post`` method is used to put a message to an input, and the ``complete`` method is used to indicate that no further messages are going to be sent to that input. Blocks which have one or more inputs also have an ``enqueue`` method which is called by the ``post`` method of all its inputs. Messages on all the inputs are enqueued onto a single input queue before they are processed. Using a single input queue allows the ``mainLoop`` method of a block to wait on data becoming available on the input queue.

.. autoclass:: pipelines.Pipeline
   :members:

.. autoclass:: pipelines.Block
   :members:
   
.. autoclass:: pipelines.BlockInput
   :members:

.. autoclass:: pipelines.SourceBlock
   :members:

.. autoclass:: pipelines.SingleInputBlock
   :members:

.. autoclass:: pipelines.ActionBlock
   :members:

.. autoclass:: pipelines.TransformBlock
   :members:

.. autoclass:: pipelines.TransformManyBlock
   :members:

.. autoclass:: pipelines.MergeBlock
   :members:

When creating a block with some functionality, it is usual to subclass from ``ActionBlock``, ``TransformBlock``, ``TransformManyBlock`` or ``MergeBlock``. In the constructor of the new block, it is necessary to call the constructor of the superclass, passing the name of a function which is used to carry out the processing of messages for the block. By convention, this function is a method of the class called ``newData``. 

For blocks with are subclassed from ``ActionBlock``, ``TransformBlock`` and ``TransformManyBlock``, ``newData(self, message)`` takes a single argument (other than self), which is the input message. 

    * For a subclass of the ``ActionBlock``, this message produces some effect, but ``newData`` does not return a value.
    
    * For a subclass of the ``TransformBlock``, one input message produces one output message, which is the return value from ``newData``
    
    * For a subclass of the ``TransformManyBlock``, one input message produces zero or more output messages. The method ``newData`` either returns a list containing the output messages or it is written as a generator which yields output messages one by one until no more remain.
    
    * Subclasses of the ``Merge`` block require a ``newData`` function that is written as a generator, and which takes several input arguments, one for each of the inputs to the merge block. Since data arrive at the inputs of a merge block asynchronously, their data are passed into newData via a collection of deques. This allows the ``newData`` function to consume as many of the input values as is required to yield an output message.
    
If the block needs to carry out some action when the pipeline is about to shut down, such as closing a file, this can be done by defining a continuation method which carries out the tidy up operation and then calls the ``defaultContinuation`` method. The ``setContinuation`` method is used to register the user-defined continuation method with the block.

    

</t>
</tnodes>
</leo_file>
