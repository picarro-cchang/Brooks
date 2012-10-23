#! /usr/bin/env python

import os.path

from waflib.Configure import conf
from waflib import Task
from waflib.TaskGen import extension, feature, after_method
from waflib.Build import BuildContext

class avrdude(Task.Task):
    def run(self):
        for asource in self.inputs:
            cmd = self.env.AVRDUDE
            cmd += ' -p ' + self.mcu
            cmd += ' -c ' + self.protocol
            cmd += ' -C ' + os.path.abspath(os.path.join('arduino',
                                                         'hardware',
                                                         'tools',
                                                         'avr',
                                                         'etc',
                                                         'avrdude.conf'))
            cmd += " -P %s" % self.port
            cmd += ' -D -Uflash:w:' + asource.relpath() + ':i'
            print cmd
            self.exec_command(cmd)

    def runnable_status(self):
		ret=super(avrdude,self).runnable_status()
		if ret==Task.SKIP_ME:
			return Task.RUN_ME
		return ret

def configure(ctx):
    cc=ctx.find_program(['avrdude'],var='AVRDUDE')

@extension('.hex')
def avrdude_hook(tskg, node):
    tsk = tskg.create_task('avrdude', node, "")
    tsk.mcu = tskg.mcu
    tsk.protocol = tskg.protocol
    tsk.port = tskg.port
    return tsk

class UploadContext(BuildContext):
	'''Upload the build outputs'''
	cmd='upload'
	fun='upload'
	variant=''
