class PrintRubyStack(gdb.Command):
    """
    print ruby_stack: ruby_stack [thread address]

    Print the Ruby call stack
    """

    def __init__(self):
        gdb.Command.__init__(self, "ruby_stack", gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL, False)
        self.string_t = None
        self.rb_thread_t = None
        self.control_frame_t = None

    def _build_types(self):
        try:
            self.control_frame_t = gdb.lookup_type('rb_control_frame_t')
            self.rb_thread_t = gdb.lookup_type('rb_thread_t')
            self.string_t = gdb.lookup_type('struct RString')
        except gdb.error:
            raise gdb.GdbError ("ruby extension requires symbols")

    def get_rstring(self, addr):
        s = addr.cast(self.string_t.pointer())
        if s['basic']['flags'] & (1 << 13):
            return s['as']['heap']['ptr'].string()
        else:
            return s['as']['ary'].string()

    def get_lineno(self, iseq, pos):
        if pos != 0:
            pos -= 1
        t = iseq['line_info_table']
        t_size = iseq['line_info_size']

        if t_size == 0:
            return 0
        elif t_size == 1:
            return t[0]['line_no']

        for i in range(0, int(t_size)):
            if pos == t[i]['position']:
                return t[i]['line_no']
            elif t[i]['position'] > pos:
                return t[i-1]['line_no']

        return t[t_size-1]['line_no']

    def print_call_stack(self, th_addr=None):
        self._build_types()

        if th_addr is None:
            th = gdb.parse_and_eval('ruby_current_thread')
        else:
            th = gdb.Value(gdb.Value(th_addr).cast(self.rb_thread_t.pointer()))

        last_cfp = th['cfp']
        # XXX AJW Skip the first two control frames. Not entirely sure why. Need to investigate more
        start_cfp = (th['stack'] + th['stack_size']).cast(self.control_frame_t.pointer()) - 2
        # NOTE stack grows downward
        num_frames = start_cfp - last_cfp + 1
        cfp = start_cfp

        call_stack = []
        for i in range(0, int(num_frames)):
            if cfp['iseq'].dereference().address != 0:
                if cfp['pc'].dereference().address != 0:
                    s = "{0}:{1}:in `{2}'".format(
                        self.get_rstring(cfp['iseq']['location']['path']),
                        self.get_lineno(cfp['iseq'], cfp['pc'] - cfp['iseq']['iseq_encoded']),
                        self.get_rstring(cfp['iseq']['location']['label'])
                    )
                    call_stack.append(s)

            cfp -= 1

        for i in reversed(call_stack):
            print(i)

    def invoke(self, arg, from_tty):
        arg_list = gdb.string_to_argv(arg)
        if len(arg_list) > 0:
            self.print_call_stack(int(arg_list[0], 16))
        else:
            self.print_call_stack()

PrintRubyStack()
