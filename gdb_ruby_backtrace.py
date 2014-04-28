def get_rstring(addr):
  s = addr.cast(string_t.pointer())
  if s['basic']['flags'] & (1 << 13):
    return s['as']['heap']['ptr'].string()
  else:
    return s['as']['ary'].string()

def get_lineno(iseq, pos):
  if pos != 0:
    pos -= 1
  t = iseq['line_info_table']
  t_size = iseq['line_info_size']

  if t_size == 0:
    return 0
  elif t_size == 1:
    return t[0]['line_no']

  for i in range(0, t_size):
    if pos == t[i]['position']:
      return t[i]['line_no']
    elif t[i]['position'] > pos:
      return t[i-1]['line_no']

  return t[t_size-1]['line_no']

try:
  control_frame_t = gdb.lookup_type('rb_control_frame_t')
  string_t = gdb.lookup_type('struct RString')
except gdb.error:
  raise gdb.GdbError ("ruby extension requires symbols")

th = gdb.parse_and_eval('ruby_current_thread')

last_cfp = th['cfp']
start_cfp = (th['stack'] + th['stack_size']).cast(control_frame_t.pointer()) - 2
size = start_cfp - last_cfp + 1
cfp = start_cfp
call_stack = []
for i in range(0, size):
  if cfp['iseq'].dereference().address != 0:
    if cfp['pc'].dereference().address != 0:
      s = "{}:{}:in `{}'".format(get_rstring(cfp['iseq']['location']['path']),
        get_lineno(cfp['iseq'], cfp['pc'] - cfp['iseq']['iseq_encoded']),
        get_rstring(cfp['iseq']['location']['label']))
      call_stack.append(s)

  cfp -= 1

for i in reversed(call_stack):
  print i

end