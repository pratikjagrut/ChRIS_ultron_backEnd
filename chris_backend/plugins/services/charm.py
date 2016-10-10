#!/usr/bin/env python3.5

"""

charm - ChRIS / pman interface.

"""

import  sys
import  os
import  pprint
import  datetime
import  socket
import  json

# from    .pman._colors       import Colors
# from    .pman.crunner       import crunner
# from    .pman.purl          import Purl

from    pman._colors       import Colors
from    pman.crunner       import crunner
from    pman.purl          import Purl

import  datetime
import  pdb

class pman_settings():
    HOST    =  [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
    PORT    = '5010'

class Charm():

    def qprint(self, msg, **kwargs):

        str_comms  = "status"
        for k,v in kwargs.items():
            if k == 'comms':    str_comms  = v

        if not self.b_quiet:
            if str_comms == 'status':   print(Colors.PURPLE,    end="")
            if str_comms == 'error':    print(Colors.RED,       end="")
            if str_comms == "tx":       print(Colors.YELLOW + "---->")
            if str_comms == "rx":       print(Colors.GREEN  + "<----")
            print('%s' % datetime.datetime.now() + " | ",       end="")
            print(msg)
            if str_comms == "tx":       print(Colors.YELLOW + "---->")
            if str_comms == "rx":       print(Colors.GREEN  + "<----")
            print(Colors.NO_COLOUR, end="")

    def col2_print(self, str_left, str_right):
        print(Colors.WHITE +
              ('%*s' % (self.LC, str_left)), end='')
        print(Colors.LIGHT_BLUE +
              ('%*s' % (self.RC, str_right)) + Colors.NO_COLOUR)

    def __init__(self, **kwargs):
        # threading.Thread.__init__(self)

        self.str_http       = ""
        self.str_ip         = ""
        self.str_port       = ""
        self.str_URL        = ""
        self.str_verb       = ""
        self.str_msg        = ""
        self.d_msg          = {}
        self.str_protocol   = "http"
        self.pp             = pprint.PrettyPrinter(indent=4)
        self.b_man          = False
        self.str_man        = ''
        self.b_quiet        = False
        self.b_raw          = False
        self.auth           = ''
        self.str_jsonwrapper= ''
        self.str_inputdir   = ''
        self.str_outputdir  = ''

        self.d_args         = {}
        self.l_appArgs      = {}
        self.c_pluginInst   = {}
        self.d_pluginRepr   = {}
        self.app            = None

        self.LC             = 40
        self.RC             = 40

        for key,val in kwargs.items():

            if key == 'app_args':       self.l_appArgs      = val
            if key == 'd_args':         self.d_args         = val
            if key == 'plugin_inst':    self.c_pluginInst   = val
            if key == 'plugin_repr':    self.d_pluginRepr   = val
            if key == 'app':            self.app            = val
            if key == 'inputdir':       self.str_inputdir   = val
            if key == 'outputdir':      self.str_outputdir  = val

        self.d_pluginInst   = vars(self.c_pluginInst)

        if not self.b_quiet:

            print(Colors.LIGHT_GREEN)
            print("""
            \t\t\t+---------------------+
            \t\t\t| Welcome to Charm.py |
            \t\t\t+---------------------+
            """)
            print(Colors.CYAN + """
            Charm is the interface class/code between ChRIS and a pman process management
            system.

            See 'charm.py --man commands' for more help.

            """)

        self.qprint('d_args         = \n%s' % self.pp.pformat(self.d_args))
        self.qprint('app_args       = %s'   % self.l_appArgs)
        self.qprint('d_pluginInst   = \n%s' % self.pp.pformat(self.d_pluginInst))
        self.qprint('d_pluginRepr   = \n%s' % self.pp.pformat(self.d_pluginRepr))
        self.qprint('app            = %s'   % self.app)
        self.qprint('inputdir       = %s'   % self.str_inputdir)
        self.qprint('outputdir      = %s'   % self.str_outputdir)
        pdb.set_trace()

    def app_manage(self, **kwargs):
        """
        Main "manager"/"dispatcher" for running plugins.
        """
        str_method  = 'internal'
        b_launched  = False
        for k,v in kwargs.items():
            if k == 'method':   str_method  = v

        if str_method == 'internal':
            self.app_launchInternal()
            b_launched  = True
        if str_method == 'crunner':
            self.app_crunner()
            b_launched  = True
        if str_method == 'pman':
            self.app_pman()

        if b_launched: self.c_pluginInst.register_output_files()

    def app_launchInternal(self):
        self.app.launch(self.l_appArgs)
        self.c_pluginInst.register_output_files()

    def app_crunner(self):
        """
        Run the "app" in a crunner instance.

        :param self:
        :return:
        """

        str_cmdLineArgs = ''.join('{} {}'.format(key, val) for key,val in sorted(self.d_args.items()))
        print(str_cmdLineArgs)

        str_allCmdLineArgs      = ' '.join(self.l_appArgs)
        str_exec                = os.path.join(self.d_pluginRepr['selfpath'], self.d_pluginRepr['selfexec'])

        if len(self.d_pluginRepr['execshell']):
            str_exec            = '%s %s' % (self.d_pluginRepr['execshell'], str_exec)

        str_cmd                 = '%s %s' % (str_exec, str_allCmdLineArgs)
        print(str_cmd)

        verbosity               = 10
        shell                   = crunner(verbosity = verbosity)

        shell.b_splitCompound   = True
        shell.b_showStdOut      = True
        shell.b_showStdErr      = True
        shell.b_echoCmd         = True

        shell(str_cmd)
        shell.jobs_loopctl()

        # self.app.launch(self.l_appArgs)
        self.c_pluginInst.register_output_files()

    def app_pman(self, *args, **kwargs):
        """
        Run the "app" via pman
        """

        print(self.d_args)
        str_cmdLineArgs = ''.join('{} {} '.format(key, val) for key,val in sorted(self.d_args.items()))
        print('in app_pman, cmdLineArg = %s' % str_cmdLineArgs)

        print('in app_pman, l_appArgs = %s' % self.l_appArgs)
        str_allCmdLineArgs      = ' '.join(self.l_appArgs)
        str_exec                = os.path.join(self.d_pluginRepr['selfpath'], self.d_pluginRepr['selfexec'])

        if len(self.d_pluginRepr['execshell']):
            str_exec            = '%s %s' % (self.d_pluginRepr['execshell'], str_exec)

        str_cmd                 = '%s %s' % (str_exec, str_allCmdLineArgs)
        print('in app_pman, cmd = %s' % str_cmd)

        d_msg = {
            'action':   'run',
            'meta': {
                        'cmd':      str_cmd,
                        'threaded': True,
                        'auid':     self.c_pluginInst.owner.username,
                        'jid':      str(self.d_pluginInst['id'])
            }
        }
        print(d_msg)

        str_http        = '%s:%s' % (pman_settings.HOST, pman_settings.PORT)
        print(str_http)

        purl    = Purl(
            msg         = json.dumps(d_msg),
            http        = str_http,
            verb        = 'POST',
            contentType = 'application/vnd.collection+json',
            b_raw       = True,
            b_quiet     = False,
            jsonwrapper = 'payload',
        )

        # run the app
        print(json.dumps(json.loads(purl()), indent=2))

    def app_statusCheckAndRegister(self, *args, **kwargs):
        """
        Check on the status of the job, and if just finished without error,
        register output files.
        """

        # First get current status
        str_status  = self.c_pluginInst.status

        # Now ask pman for the job status
        d_msg   = {
            "action": "status",
            "meta": {
                    "key":      "jid",
                    "value":    str(self.d_pluginInst['id'])
            }
        }
        str_http        = '%s:%s' % (pman_settings.HOST, pman_settings.PORT)

        purl    = Purl(
            msg         = json.dumps(d_msg),
            http        = str_http,
            verb        = 'POST',
            contentType = 'application/vnd.collection+json',
            b_raw       = True,
            b_quiet     = False,
            jsonwrapper = 'payload',
        )

        d_pman          = json.loads(purl())
        str_pmanStatus  = d_pman['d_ret']['l_status'][0]
        str_DBstatus    = self.c_pluginInst.status
        self.qprint('Current job DB   status = %s' % str_DBstatus,          comms = 'status')
        self.qprint('Current job pman status = %s' % str_pmanStatus,        comms = 'status')
        if 'finished' in str_pmanStatus and str_pmanStatus != str_DBstatus:
            self.qprint('Registering output files...', comms = 'status')
            self.c_pluginInst.register_output_files()
            self.c_pluginInst.status    = str_pmanStatus
            self.c_pluginInst.end_date  = datetime.datetime.now()
            self.c_pluginInst.save()
            self.qprint("Saving job DB status   as '%s'" %  str_pmanStatus,
                                                            comms = 'status')
            self.qprint("Saving job DB end_date as '%s'" %  self.c_pluginInst.end_date,
                                                            comms = 'status')
        if str_pmanStatus == 'finishedWithError': self.app_handleRemoteError()


    def app_handleRemoteError(self, *args, **kwargs):
        """
        Collect the 'stderr' from the remote app
        """

        str_deepVal = ''

        def str_deepnest(d):
            nonlocal str_deepVal
            for k, v in d.items():
                if isinstance(v, dict):
                    str_deepnest(v)
                else:
                    str_deepVal = '%s' % ("{0} : {1}".format(k, v))
                    # str_deepVal = v

        # Collect the 'stderr' from pman for this instance
        d_msg   = {
            "action": "search",
            "meta": {
                "key":      "jid",
                "value":    str(self.d_pluginInst['id']),
                "job":      "0",
                "when":     "end",
                "field":    "stderr"
            }
        }
        str_http        = '%s:%s' % (pman_settings.HOST, pman_settings.PORT)

        purl    = Purl(
            msg         = json.dumps(d_msg),
            http        = str_http,
            verb        = 'POST',
            contentType = 'application/vnd.collection+json',
            b_raw       = True,
            b_quiet     = False,
            jsonwrapper = 'payload',
        )

        self.str_deep   = ''
        d_pman          = json.loads(purl())
        str_deepnest(d_pman['d_ret'])
        self.qprint(str_deepVal, comms = 'error')

        purl.d_msg['meta']['field'] = 'returncode'
        d_pman          = json.loads(purl())
        str_deepnest(d_pman['d_ret'])
        self.qprint(str_deepVal, comms = 'error')

if __name__ == '__main__':

    str_defIP = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
    str_defPort = 5010

    parser  = argparse.ArgumentParser(description = 'interface between ChRIS and pman')

    sys.exit(0)
