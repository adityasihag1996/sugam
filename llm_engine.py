from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

import llm_engine_config

class LLM_engine:
    def __init__(self):
        if llm_engine_config.USE_4BIT:
            bnb_config = BitsAndBytesConfig(
                            load_in_8bit = False,
                            load_in_4bit = True,
                            bnb_4bit_quant_type = "nf4",
                            bnb_4bit_compute_dtype = "float16",
                            bnb_4bit_use_double_quant = False,
                        )
        elif llm_engine_config.USE_8BIT:
            bnb_config = BitsAndBytesConfig(
                            load_in_8bit = True,
                        )
        else:
            bnb_config = None

        self.tokenizer = AutoTokenizer.from_pretrained(
                        llm_engine_config.MODEL_ID,
                        token = llm_engine_config.HF_TOKEN,
                    )
        
        self.model = AutoModelForCausalLM.from_pretrained(
                    llm_engine_config.MODEL_ID,
                    device_map = "auto",
                    token = llm_engine_config.HF_TOKEN,
                    attn_implementation = "flash_attention_2" if llm_engine_config.USE_FLASH_ATTN else "eager",
                    low_cpu_mem_usage = True,
                    quantization_config = bnb_config,
                    torch_dtype = torch.float16 if bnb_config == None else None,
                )
        
    def tokenise(self, text, add_special_tokens = False):
        input_ids = self.tokenizer.encode(text, add_special_tokens = add_special_tokens)

        return input_ids
        
    def apply_chat_template(self, system_prompt, user_message, return_pt = False):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
                
        chat = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt = True,
            tokenize = False,
        )

        input_ids = self.tokenise(chat)

        if return_pt:
            input_ids = torch.tensor([input_ids])

        return input_ids
        
    def forward(self, input_ids):
        terminators = [
            self.tokenizer.eos_token_id,
            self.tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        outputs = self.model.generate(
                    input_ids,
                    attention_mask = torch.ones_like(input_ids),
                    max_new_tokens = 512,
                    eos_token_id = terminators,
                    pad_token_id = self.tokenizer.eos_token_id,
                    do_sample = True,
                    temperature = 0.3,
                    top_p = 0.9,
                )

        response = outputs[0][input_ids.shape[-1]:]
        response_decoded = self.tokenizer.decode(response, skip_special_tokens = True)

        return response_decoded

