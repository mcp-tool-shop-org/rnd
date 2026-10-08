import sys, torch, peft
from transformers import LlamaConfig, LlamaForCausalLM
dev = sys.argv[1]
torch.manual_seed(0)
cfg = LlamaConfig(vocab_size=2048, hidden_size=256, intermediate_size=704, num_hidden_layers=4, num_attention_heads=8, num_key_value_heads=4, max_position_embeddings=512)
m = LlamaForCausalLM(cfg).to(dev, torch.bfloat16)
m = peft.get_peft_model(m, peft.LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"]))
opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=5e-3)
ids = torch.arange(256, device=dev).repeat(8, 1) % 97
ls = []
for _ in range(30):
    o = m(input_ids=ids, labels=ids); opt.zero_grad(); o.loss.backward(); opt.step(); ls.append(round(float(o.loss), 4))
print(dev, ls[0], ls[9], ls[19], ls[-1])
