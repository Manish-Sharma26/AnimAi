import json, sys

with open('outputs/failure_logs/20260413_075829_tts_synthesis_failed.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Print all keys
sys.stdout.buffer.write(('Keys: ' + str(list(d.keys())) + '\n\n').encode('utf-8'))
# Print full error
err = d.get('error', '')
sys.stdout.buffer.write(('FULL ERROR (last 1500 chars):\n' + err[-1500:] + '\n\n').encode('utf-8'))
# Print stdout (contains manim logs including Azure TTS error details)
stdout = d.get('stdout', '') or d.get('manim_stdout', '') or d.get('sandbox_output', '')
sys.stdout.buffer.write(('STDOUT:\n' + stdout[:1500] + '\n').encode('utf-8'))
