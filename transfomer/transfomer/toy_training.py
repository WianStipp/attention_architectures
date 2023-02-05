"""Toy training script to make sure the model is learning as expected."""

from typing import List, Tuple, NamedTuple, Sequence
import random
import torch as T
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from transfomer import modeling

MAX_TRAINING_SEQ_LEN = 32
PAD_TOK = 0
START_TOK = 0
EOS_TOK = 1

# TRAINING ARGS
BATCH_SIZE = 8

class TrainingPoint(NamedTuple):
  encoder_tokens: T.Tensor
  decoder_tokens: T.Tensor
  target_token: T.Tensor

class ToyDataset(Dataset):
  def __init__(self, input_output_sequences: List[Tuple[T.Tensor, T.Tensor]]) -> None:
    self.input_output_sequences = input_output_sequences
    self._prepare_data()

  def _prepare_data(self) -> None:
    self.data = []
    for input, target in self.input_output_sequences:
      input = apply_start_end_tokens(input)
      target = apply_start_end_tokens(target)
      for i in range(1, len(target)):
        t = target[i]
        decode_toks = target[:i]
        self.data.append(TrainingPoint(input, decode_toks, t))

  def __len__(self) -> int:
    return len(self.data)

  def __getitem__(self, index) -> TrainingPoint:
    return self.data[index]

def collate_trainingpoints(trainingpoints: Sequence[TrainingPoint]) -> TrainingPoint:
  encoder_toks = [t.encoder_tokens for t in trainingpoints]
  decoder_toks = [t.decoder_tokens for t in trainingpoints]
  target_toks = T.concat([t.target_token[None] for t in trainingpoints], dim=0)
  max_encoder_len = len(max(encoder_toks, key=len))
  max_decoder_len = len(max(decoder_toks, key=len))
  encoder_toks = T.vstack([F.pad(input=e, pad=(0,max_encoder_len - len(e)), mode='constant', value=PAD_TOK) for e in encoder_toks])
  decoder_toks = T.vstack([F.pad(d, (max_decoder_len - len(d),0), 'constant', PAD_TOK) for d in decoder_toks])
  return TrainingPoint(encoder_toks, decoder_toks, target_toks)

def make_dataset(n_examples: int, max_vocab_tok: int):
  """
  Toy dataset where we encode a random sequence, and the task is to decode it backwards.
  I.e. (1,8,12,9) -> (9,12,8,1)
  """
  input_output_sequences: List[Tuple[T.Tensor, T.Tensor]] = []
  for _ in range(n_examples):
    seq_len = random.randint(1, MAX_TRAINING_SEQ_LEN)
    x = T.randint(low=1, high=max_vocab_tok+1, size=(seq_len, )).type(T.long)
    y = T.flip(x, (0, ))
    input_output_sequences.append((x,y))
  return ToyDataset(input_output_sequences)

def apply_start_end_tokens(x: T.Tensor, include_end: bool = True) -> T.Tensor:
  if include_end:
    return T.concat([T.Tensor((START_TOK, )), x, T.Tensor((EOS_TOK, ))], dim=0).type(T.long)
  return T.concat([T.Tensor((START_TOK, )), x], dim=0).type(T.long)

def main() -> None:
  config = modeling.TransfomerConfig(vocab_size=100, d_model=512, d_k=64, d_v=64, n_attn_heads_in_encoder=8,\
                                      n_attn_heads_in_decoder=8, n_decoder_blocks=6, n_encoder_blocks=6, dim_feedfwd=2048\
                                    )
  model = modeling.Transformer(config)
  dataset = make_dataset(1000, max_vocab_tok=config.vocab_size)
  dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_trainingpoints)

  for b in dataloader:
    print(b)
    break

if __name__ == '__main__':
  main()
