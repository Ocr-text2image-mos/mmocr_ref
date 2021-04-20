import math

import torch
import torch.nn as nn

from mmocr.models.ner.utils.activations import ACT2FN


class BertModel(nn.Module):

    def __init__(self,
                 num_hidden_layers=12,
                 initializer_range=0.02,
                 vocab_size=21128,
                 hidden_size=768,
                 max_position_embeddings=128,
                 type_vocab_size=2,
                 layer_norm_eps=1e-12,
                 hidden_dropout_prob=0.1,
                 output_attentions=False,
                 output_hidden_states=False,
                 num_attention_heads=12,
                 attention_probs_dropout_prob=0.1,
                 intermediate_size=3072,
                 hidden_act='gelu_new'):
        super(BertModel, self).__init__()
        self.embeddings = BertEmbeddings(
            vocab_size=vocab_size,
            hidden_size=hidden_size,
            max_position_embeddings=max_position_embeddings,
            type_vocab_size=type_vocab_size,
            layer_norm_eps=layer_norm_eps,
            hidden_dropout_prob=hidden_dropout_prob)
        self.encoder = BertEncoder(
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            num_hidden_layers=num_hidden_layers,
            hidden_size=hidden_size,
            num_attention_heads=num_attention_heads,
            attention_probs_dropout_prob=attention_probs_dropout_prob,
            layer_norm_eps=layer_norm_eps,
            hidden_dropout_prob=hidden_dropout_prob,
            intermediate_size=intermediate_size,
            hidden_act=hidden_act)
        self.pooler = BertPooler(hidden_size=hidden_size)
        self.num_hidden_layers = num_hidden_layers
        self.initializer_range = initializer_range
        self.init_weights()

    def _resize_token_embeddings(self, new_num_tokens):
        old_embeddings = self.embeddings.word_embeddings
        new_embeddings = self._get_resized_embeddings(old_embeddings,
                                                      new_num_tokens)
        self.embeddings.word_embeddings = new_embeddings
        return self.embeddings.word_embeddings

    def forward(self,
                input_ids,
                attention_mask=None,
                token_type_ids=None,
                position_ids=None,
                head_mask=None):
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)
        if token_type_ids is None:
            token_type_ids = torch.zeros_like(input_ids)
        extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
        extended_attention_mask = extended_attention_mask.to(
            dtype=next(self.parameters()).dtype)
        extended_attention_mask = (1.0 - extended_attention_mask) * -10000.0
        if head_mask is not None:
            if head_mask.dim() == 1:
                head_mask = head_mask.unsqueeze(0).unsqueeze(0).unsqueeze(
                    -1).unsqueeze(-1)
                head_mask = head_mask.expand(self.num_hidden_layers, -1, -1,
                                             -1, -1)
            elif head_mask.dim() == 2:
                head_mask = head_mask.unsqueeze(1).unsqueeze(-1).unsqueeze(-1)
            head_mask = head_mask.to(dtype=next(self.parameters()).dtype)
        else:
            head_mask = [None] * self.num_hidden_layers

        embedding_output = self.embeddings(
            input_ids,
            position_ids=position_ids,
            token_type_ids=token_type_ids)
        encoder_outputs = self.encoder(
            embedding_output, extended_attention_mask, head_mask=head_mask)
        sequence_output = encoder_outputs[0]
        pooled_output = self.pooler(sequence_output)

        # add hidden_states and attentions if they are here
        # sequence_output, pooled_output, (hidden_states), (attentions)
        outputs = (
            sequence_output,
            pooled_output,
        ) + encoder_outputs[1:]
        return outputs

    def _init_weights(self, module):
        """Initialize the weights."""
        if isinstance(module, (nn.Linear, nn.Embedding)):
            # Slightly different from the TF version which
            # uses truncated_normal for initialization
            # cf https://github.com/pytorch/pytorch/pull/5617
            module.weight.data.normal_(mean=0.0, std=self.initializer_range)
        elif isinstance(module, BertLayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)
        if isinstance(module, nn.Linear) and module.bias is not None:
            module.bias.data.zero_()

    def init_weights(self):
        """Initialize and prunes weights if needed."""
        # Initialize weights
        self.apply(self._init_weights)


BertLayerNorm = torch.nn.LayerNorm


class BertEmbeddings(nn.Module):
    """Construct the embeddings from word, position and token_type
    embeddings."""

    def __init__(self,
                 vocab_size=21128,
                 hidden_size=768,
                 max_position_embeddings=128,
                 type_vocab_size=2,
                 layer_norm_eps=1e-12,
                 hidden_dropout_prob=0.1):
        super(BertEmbeddings, self).__init__()

        self.word_embeddings = nn.Embedding(
            vocab_size, hidden_size, padding_idx=0)
        self.position_embeddings = nn.Embedding(max_position_embeddings,
                                                hidden_size)
        self.token_type_embeddings = nn.Embedding(type_vocab_size, hidden_size)

        # self.LayerNorm is not snake-cased to stick with
        # TensorFlow model variable name and be able to load
        # any TensorFlow checkpoint file
        self.LayerNorm = BertLayerNorm(hidden_size, eps=layer_norm_eps)
        self.dropout = nn.Dropout(hidden_dropout_prob)

    def forward(self, input_ids, token_type_ids=None, position_ids=None):
        seq_length = input_ids.size(1)
        if position_ids is None:
            position_ids = torch.arange(
                seq_length, dtype=torch.long, device=input_ids.device)
            position_ids = position_ids.unsqueeze(0).expand_as(input_ids)
            # import numpy as np
            # np.save("npys/position_id.npy", position_ids.cpu().numpy())
        if token_type_ids is None:
            token_type_ids = torch.zeros_like(input_ids)

        words_emb = self.word_embeddings(input_ids)
        position_emb = self.position_embeddings(position_ids)
        token_type_emb = self.token_type_embeddings(token_type_ids)
        embeddings = words_emb + position_emb + token_type_emb
        embeddings = self.LayerNorm(embeddings)
        embeddings = self.dropout(embeddings)
        return embeddings


class BertEncoder(nn.Module):

    def __init__(self,
                 output_attentions=False,
                 output_hidden_states=False,
                 num_hidden_layers=12,
                 hidden_size=768,
                 num_attention_heads=12,
                 attention_probs_dropout_prob=0.1,
                 layer_norm_eps=1e-12,
                 hidden_dropout_prob=0.1,
                 intermediate_size=3072,
                 hidden_act='gelu_new'):
        super(BertEncoder, self).__init__()
        self.output_attentions = output_attentions
        self.output_hidden_states = output_hidden_states
        self.layer = nn.ModuleList([
            BertLayer(
                hidden_size=hidden_size,
                num_attention_heads=num_attention_heads,
                output_attentions=output_attentions,
                attention_probs_dropout_prob=attention_probs_dropout_prob,
                layer_norm_eps=layer_norm_eps,
                hidden_dropout_prob=hidden_dropout_prob,
                intermediate_size=intermediate_size,
                hidden_act=hidden_act) for _ in range(num_hidden_layers)
        ])

    def forward(self, hidden_states, attention_mask=None, head_mask=None):
        all_hidden_states = ()
        all_attentions = ()
        for i, layer_module in enumerate(self.layer):
            if self.output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states, )

            layer_outputs = layer_module(hidden_states, attention_mask,
                                         head_mask[i])
            hidden_states = layer_outputs[0]

            if self.output_attentions:
                all_attentions = all_attentions + (layer_outputs[1], )

        # Add last layer
        if self.output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states, )

        outputs = (hidden_states, )
        if self.output_hidden_states:
            outputs = outputs + (all_hidden_states, )
        if self.output_attentions:
            outputs = outputs + (all_attentions, )
        # last-layer hidden state, (all hidden states), (all attentions)
        return outputs


class BertPooler(nn.Module):

    def __init__(self, hidden_size=768):
        super(BertPooler, self).__init__()
        self.dense = nn.Linear(hidden_size, hidden_size)
        self.activation = nn.Tanh()

    def forward(self, hidden_states):
        # We "pool" the model by simply taking the hidden state corresponding
        # to the first token.
        first_token_tensor = hidden_states[:, 0]
        pooled_output = self.dense(first_token_tensor)
        pooled_output = self.activation(pooled_output)
        return pooled_output


class BertLayer(nn.Module):

    def __init__(self,
                 hidden_size=768,
                 num_attention_heads=12,
                 output_attentions=False,
                 attention_probs_dropout_prob=0.1,
                 layer_norm_eps=1e-12,
                 hidden_dropout_prob=0.1,
                 intermediate_size=3072,
                 hidden_act='gelu_new'):
        super(BertLayer, self).__init__()
        self.attention = BertAttention(
            hidden_size=hidden_size,
            num_attention_heads=num_attention_heads,
            output_attentions=output_attentions,
            attention_probs_dropout_prob=attention_probs_dropout_prob,
            layer_norm_eps=layer_norm_eps,
            hidden_dropout_prob=hidden_dropout_prob)
        self.intermediate = BertIntermediate(
            hidden_size=hidden_size,
            intermediate_size=intermediate_size,
            hidden_act=hidden_act)
        self.output = BertOutput(
            intermediate_size=intermediate_size,
            hidden_size=hidden_size,
            layer_norm_eps=layer_norm_eps,
            hidden_dropout_prob=hidden_dropout_prob)

    def forward(self, hidden_states, attention_mask=None, head_mask=None):
        attention_outputs = self.attention(hidden_states, attention_mask,
                                           head_mask)
        attention_output = attention_outputs[0]
        intermediate_output = self.intermediate(attention_output)
        layer_output = self.output(intermediate_output, attention_output)
        outputs = (layer_output, ) + attention_outputs[
            1:]  # add attentions if we output them
        return outputs


class BertSelfAttention(nn.Module):

    def __init__(self,
                 hidden_size=768,
                 num_attention_heads=12,
                 output_attentions=False,
                 attention_probs_dropout_prob=0.1):
        super(BertSelfAttention, self).__init__()
        if hidden_size % num_attention_heads != 0:
            raise ValueError('The hidden size (%d) is not a multiple of'
                             'the number of attention heads (%d)' %
                             (hidden_size, num_attention_heads))
        self.output_attentions = output_attentions

        self.num_attention_heads = num_attention_heads
        self.att_head_size = int(hidden_size / num_attention_heads)
        self.all_head_size = self.num_attention_heads * self.att_head_size

        self.query = nn.Linear(hidden_size, self.all_head_size)
        self.key = nn.Linear(hidden_size, self.all_head_size)
        self.value = nn.Linear(hidden_size, self.all_head_size)

        self.dropout = nn.Dropout(attention_probs_dropout_prob)

    def transpose_for_scores(self, x):
        new_x_shape = x.size()[:-1] + (self.num_attention_heads,
                                       self.att_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(self, hidden_states, attention_mask=None, head_mask=None):
        mixed_query_layer = self.query(hidden_states)
        mixed_key_layer = self.key(hidden_states)
        mixed_value_layer = self.value(hidden_states)

        query_layer = self.transpose_for_scores(mixed_query_layer)
        key_layer = self.transpose_for_scores(mixed_key_layer)
        value_layer = self.transpose_for_scores(mixed_value_layer)

        # Take the dot product between "query" and
        # "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer,
                                        key_layer.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.att_head_size)
        if attention_mask is not None:
            # Apply the attention mask is (precomputed for
            # all layers in BertModel forward() function)
            attention_scores = attention_scores + attention_mask

        # Normalize the attention scores to probabilities.
        attention_probs = nn.Softmax(dim=-1)(attention_scores)

        # This is actually dropping out entire tokens to attend to, which might
        # seem a bit unusual, but is taken from the original Transformer paper.
        attention_probs = self.dropout(attention_probs)

        # Mask heads if we want to
        if head_mask is not None:
            attention_probs = attention_probs * head_mask

        context_layer = torch.matmul(attention_probs, value_layer)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (
            self.all_head_size, )
        context_layer = context_layer.view(*new_context_layer_shape)

        outputs = (context_layer,
                   attention_probs) if self.output_attentions else (
                       context_layer, )
        return outputs


class BertSelfOutput(nn.Module):

    def __init__(self,
                 hidden_size=768,
                 layer_norm_eps=1e-12,
                 hidden_dropout_prob=0.1):
        super(BertSelfOutput, self).__init__()
        self.dense = nn.Linear(hidden_size, hidden_size)
        self.LayerNorm = BertLayerNorm(hidden_size, eps=layer_norm_eps)
        self.dropout = nn.Dropout(hidden_dropout_prob)

    def forward(self, hidden_states, input_tensor):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.LayerNorm(hidden_states + input_tensor)
        return hidden_states


def prune_linear_layer(layer, index, dim=0):
    """Prune a linear layer (a model parameters) to keep only entries in index.

    Return the pruned layer as a new layer with requires_grad=True. Used to
    remove heads.
    """
    index = index.to(layer.weight.device)
    W = layer.weight.index_select(dim, index).clone().detach()
    if layer.bias is not None:
        if dim == 1:
            b = layer.bias.clone().detach()
        else:
            b = layer.bias[index].clone().detach()
    new_size = list(layer.weight.size())
    new_size[dim] = len(index)
    new_layer = nn.Linear(
        new_size[1], new_size[0], bias=layer.bias
        is not None).to(layer.weight.device)
    new_layer.weight.requires_grad = False
    new_layer.weight.copy_(W.contiguous())
    new_layer.weight.requires_grad = True
    if layer.bias is not None:
        new_layer.bias.requires_grad = False
        new_layer.bias.copy_(b.contiguous())
        new_layer.bias.requires_grad = True
    return new_layer


class BertAttention(nn.Module):

    def __init__(self,
                 hidden_size=768,
                 num_attention_heads=12,
                 output_attentions=False,
                 attention_probs_dropout_prob=0.1,
                 layer_norm_eps=1e-12,
                 hidden_dropout_prob=0.1):
        super(BertAttention, self).__init__()
        self.self = BertSelfAttention(
            hidden_size=hidden_size,
            num_attention_heads=num_attention_heads,
            output_attentions=output_attentions,
            attention_probs_dropout_prob=attention_probs_dropout_prob)
        self.output = BertSelfOutput(
            hidden_size=hidden_size,
            layer_norm_eps=layer_norm_eps,
            hidden_dropout_prob=hidden_dropout_prob)
        self.pruned_heads = set()

    def prune_heads(self, heads):
        if len(heads) == 0:
            return
        mask = torch.ones(self.self.num_attention_heads,
                          self.self.attention_head_size)
        # Convert to set and emove already pruned heads
        heads = set(heads) - self.pruned_heads
        for head in heads:
            # Compute how many pruned heads are before the head
            # and move the index accordingly
            head = head - sum(1 if h < head else 0 for h in self.pruned_heads)
            mask[head] = 0
        mask = mask.view(-1).contiguous().eq(1)
        index = torch.arange(len(mask))[mask].long()

        # Prune linear layers
        self.self.query = prune_linear_layer(self.self.query, index)
        self.self.key = prune_linear_layer(self.self.key, index)
        self.self.value = prune_linear_layer(self.self.value, index)
        self.output.dense = prune_linear_layer(self.output.dense, index, dim=1)

        # Update hyper params and store pruned heads
        self.self.num_attention_heads = self.self.num_attention_heads - len(
            heads)
        tmp = self.self.attention_head_size * self.self.num_attention_heads
        self.self.all_head_size = tmp
        self.pruned_heads = self.pruned_heads.union(heads)

    def forward(self, input_tensor, attention_mask=None, head_mask=None):
        self_outputs = self.self(input_tensor, attention_mask, head_mask)
        attention_output = self.output(self_outputs[0], input_tensor)
        outputs = (attention_output,
                   ) + self_outputs[1:]  # add attentions if we output them
        return outputs


class BertIntermediate(nn.Module):

    def __init__(self,
                 hidden_size=768,
                 intermediate_size=3072,
                 hidden_act='gelu_new'):
        super(BertIntermediate, self).__init__()
        self.dense = nn.Linear(hidden_size, intermediate_size)
        if isinstance(hidden_act, str):
            self.intermediate_act_fn = ACT2FN[hidden_act]
        else:
            self.intermediate_act_fn = hidden_act

    def forward(self, hidden_states):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.intermediate_act_fn(hidden_states)
        return hidden_states


class BertOutput(nn.Module):

    def __init__(self,
                 intermediate_size=3072,
                 hidden_size=768,
                 layer_norm_eps=1e-12,
                 hidden_dropout_prob=0.1):

        super(BertOutput, self).__init__()
        self.dense = nn.Linear(intermediate_size, hidden_size)
        self.LayerNorm = BertLayerNorm(hidden_size, eps=layer_norm_eps)
        self.dropout = nn.Dropout(hidden_dropout_prob)

    def forward(self, hidden_states, input_tensor):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.LayerNorm(hidden_states + input_tensor)
        return hidden_states
