from typing import List
import torch as T
import torch.nn as nn

class MultiHeadAttention(nn.Module):
  def __init__(self, d_model: int, d_k: int, d_v: int, d_o:int, n_heads: int) -> None:
    super().__init__()
    self.d_model = d_model
    self.d_k = d_k
    self.d_v = d_v
    self.d_o = d_o
    self.heads: List[Attention] = [Attention(d_model, d_k, d_v) for _ in range(n_heads)]
    self.output_projection = nn.Linear(n_heads * d_v, d_model)

  def forward(self, Q: T.Tensor, K: T.Tensor, V: T.Tensor) -> T.Tensor:
    head_outputs = T.concat([head(Q, K, V) for head in self.heads], dim=-1)
    return self.output_projection(head_outputs)

class Attention(nn.Module):
  def __init__(self, d_model: int, d_k: int, d_v: int) -> None:
    super().__init__()
    self.d_model = d_model
    self.d_k = d_k
    self.d_v = d_v
    self.query_projection = nn.Linear(d_model, d_k)
    self.key_projection = nn.Linear(d_model, d_k)
    self.value_projection = nn.Linear(d_model, d_v)

  def forward(self, Q: T.Tensor, K: T.Tensor, V: T.Tensor) -> T.Tensor:
    """Compute attention given the query, keys and values.
    Args:
      Q: BS * n_tokens * model_dims
      K: BS * n_tokens * model_dims
      V: BS * n_tokens * model_dims
    """
    QW = self.query_projection(Q)
    KW = self.key_projection(K)
    VW = self.value_projection(V)
    return T.bmm(T.softmax(T.bmm(QW, T.swapaxes(KW, -1, -2)), dim=-1) / self.d_k ** 1/2, VW)

if __name__ == "__main__":
  batch_size, n_tokens = 8, 69
  d_model, d_k, d_v, d_o, n_heads = 512, 64, 64, 64, 8
  attn = Attention(d_model, d_k, d_v)
  Q = T.randn(batch_size, n_tokens, d_model)
  K = T.randn(batch_size, n_tokens, d_model)
  V = T.randn(batch_size, n_tokens, d_model)
  outputs = attn(Q, K, V)
  print(outputs)
  print(outputs.shape)

  multihead_attn = MultiHeadAttention(d_model, d_k, d_v, n_heads * d_v, n_heads)
  outputs = multihead_attn(Q, K, V)
  print(outputs)
  print(outputs.shape)