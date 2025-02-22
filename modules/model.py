from typing import Optional, List, Tuple

from modules.device import torch_gc
from modules.options import cmd_opts

tokenizer = None
model = None


def prepare_model():
    global model
    if cmd_opts.cpu:
        if cmd_opts.precision == "fp32":
            model = model.float()
        elif cmd_opts.precision == "fp16":
            model = model.bfloat16()
        else:            
            print("--precision ERROR: INT modes are only for CUDA GPUs.")
            exit(1)
    else:
        if cmd_opts.precision == "fp16":
            model = model.half().cuda()
        elif cmd_opts.precision == "int4":
            model = model.half().quantize(4).cuda()
        elif cmd_opts.precision == "int8":
            model = model.half().quantize(8).cuda()
        elif cmd_opts.precision == "fp32":
            print("--precision ERROR: fp32 mode is only for CPU. Are you really ready to have such a large amount of vmem XD")
            exit(1)

    model = model.eval()


def load_model():
    if cmd_opts.ui_dev:
        return

    from transformers import AutoModel, AutoTokenizer

    global tokenizer, model

    tokenizer = AutoTokenizer.from_pretrained(cmd_opts.model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(cmd_opts.model_path, trust_remote_code=True)
    prepare_model()


def infer(query,
          history: Optional[List[Tuple]],
          max_length, top_p, temperature):
    if cmd_opts.ui_dev:
        return "hello", "hello, dev mode!"

    if not model:
        raise "Model not loaded"

    if history is None:
        history = []

    output_pos = 0

    for output, history in model.stream_chat(
        tokenizer, query=query, history=history,
        max_length=max_length,
        top_p=top_p,
        temperature=temperature
    ):
        try:
            print(output[output_pos:],end='')
        except:
            pass
        output_pos = len(output)
        yield query, output

    print()
    torch_gc()
