"""
Custom Optimizers Module
Implements custom optimization algorithms for training neural networks.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Optional, Dict, Any
import numpy as np

from core.logger import logger


class AdamW(optim.Optimizer):
    """
    AdamW Optimizer with weight decay.
    
    Implements Adam with decoupled weight decay (AdamW) as described in:
    "Decoupled Weight Decay Regularization" (Loshchilov & Hutter, 2019).
    """

    def __init__(
        self,
        params,
        lr: float = 0.001,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.01,
        amsgrad: bool = False,
    ):
        """
        Initialize AdamW optimizer.

        Args:
            params: Model parameters.
            lr: Learning rate.
            betas: Coefficients used for computing running averages of gradient and its square.
            eps: Term added to the denominator to improve numerical stability.
            weight_decay: Weight decay coefficient.
            amsgrad: Whether to use the AMSGrad variant.
        """
        if not 0.0 <= lr:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= eps:
            raise ValueError(f"Invalid epsilon value: {eps}")
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 0: {betas[0]}")
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 1: {betas[1]}")
        if not 0.0 <= weight_decay:
            raise ValueError(f"Invalid weight_decay value: {weight_decay}")

        defaults = dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay, amsgrad=amsgrad)
        super(AdamW, self).__init__(params, defaults)

        self.amsgrad = amsgrad

    def step(self, closure: Optional[Callable] = None) -> Optional[float]:
        """Perform a single optimization step."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            for p in group['params']:
                if p.grad is None:
                    continue

                # Decoupled weight decay
                if group['weight_decay'] != 0:
                    p.data.mul_((1 - group['lr'] * group['weight_decay']))

                grad = p.grad.data

                # Decay the first and second moment running average coefficient
                if 'm' not in self.state[p]:
                    self.state[p]['m'] = torch.zeros_like(p.data)
                    self.state[p]['v'] = torch.zeros_like(p.data)

                m, v = self.state[p]['m'], self.state[p]['v']
                beta1, beta2 = group['betas']

                m.mul_(beta1).add_(grad, alpha=1 - beta1)
                v.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)

                if self.amsgrad:
                    # Maintains the maximum of all 2nd moment running avg till now
                    v_max = self.state[p].get('max_v', torch.zeros_like(v))
                    torch.maximum(v_max, v, out=v_max)
                    self.state[p]['max_v'] = v_max
                    v = v_max

                # Compute bias-corrected first moment estimate
                m_hat = m / (1 - beta1 ** self.state[p]['step'])

                # Compute bias-corrected second raw moment estimate
                v_hat = v / (1 - beta2 ** self.state[p]['step'])

                # Update parameters
                p.data.addcdiv_(m_hat, torch.sqrt(v_hat).add_(group['eps']), value=-group['lr'])

        return loss


class SGDW(optim.Optimizer):
    """
    SGD with Weight Decay.
    
    Implements SGD with decoupled weight decay.
    """

    def __init__(
        self,
        params,
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        dampening: float = 0.0,
        nesterov: bool = False,
    ):
        """
        Initialize SGDW optimizer.

        Args:
            params: Model parameters.
            lr: Learning rate.
            momentum: Momentum factor.
            weight_decay: Weight decay coefficient.
            dampening: Dampening for momentum.
            nesterov: Enables Nesterov momentum.
        """
        if not 0.0 <= lr:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= momentum:
            raise ValueError(f"Invalid momentum value: {momentum}")
        if not 0.0 <= weight_decay:
            raise ValueError(f"Invalid weight_decay value: {weight_decay}")
        if not 0.0 <= dampening:
            raise ValueError(f"Invalid dampening value: {dampening}")

        defaults = dict(
            lr=lr,
            momentum=momentum,
            dampening=dampening,
            weight_decay=weight_decay,
            nesterov=nesterov,
        )
        super(SGDW, self).__init__(params, defaults)

        if nesterov and (momentum <= 0 or dampening != 0):
            raise ValueError("Nesterov momentum requires a momentum and zero dampening")

    def step(self, closure: Optional[Callable] = None) -> Optional[float]:
        """Perform a single optimization step."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            weight_decay = group['weight_decay']
            momentum = group['momentum']
            dampening = group['dampening']
            nesterov = group['nesterov']
            lr = group['lr']

            for p in group['params']:
                if p.grad is None:
                    continue

                # Decoupled weight decay
                if weight_decay != 0:
                    p.data.mul_((1 - lr * weight_decay))

                d_p = p.grad.data

                if momentum != 0:
                    if 'momentum_buffer' not in self.state[p]:
                        buf = self.state[p]['momentum_buffer'] = torch.zeros_like(p.data)
                    else:
                        buf = self.state[p]['momentum_buffer']

                    buf.mul_(momentum).add_(d_p, alpha=1 - dampening)

                    if nesterov:
                        d_p = d_p.add(momentum, buf)
                    else:
                        d_p = buf

                p.data.add_(d_p, alpha=-lr)

        return loss


class RAdam(optim.Optimizer):
    """
    Rectified Adam Optimizer.
    
    Implements the RAdam optimizer as described in:
    "On the Variance of the Adaptive Learning Rate and Beyond" (Liu et al., 2019).
    """

    def __init__(
        self,
        params,
        lr: float = 0.001,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.0,
        degenerated_to_sgd: bool = True,
    ):
        """
        Initialize RAdam optimizer.

        Args:
            params: Model parameters.
            lr: Learning rate.
            betas: Coefficients used for computing running averages of gradient and its square.
            eps: Term added to the denominator to improve numerical stability.
            weight_decay: Weight decay coefficient.
            degenerated_to_sgd: Whether to degenerate to SGD when rectified condition is not met.
        """
        if not 0.0 <= lr:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= eps:
            raise ValueError(f"Invalid epsilon value: {eps}")
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 0: {betas[0]}")
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 1: {betas[1]}")
        if not 0.0 <= weight_decay:
            raise ValueError(f"Invalid weight_decay value: {weight_decay}")

        defaults = dict(
            lr=lr,
            betas=betas,
            eps=eps,
            weight_decay=weight_decay,
            degenerated_to_sgd=degenerated_to_sgd,
        )
        super(RAdam, self).__init__(params, defaults)

    def step(self, closure: Optional[Callable] = None) -> Optional[float]:
        """Perform a single optimization step."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            for p in group['params']:
                if p.grad is None:
                    continue

                # Decoupled weight decay
                if group['weight_decay'] != 0:
                    p.data.mul_((1 - group['lr'] * group['weight_decay']))

                grad = p.grad.data
                if grad.is_sparse:
                    raise RuntimeError('RAdam does not support sparse gradients')

                state = self.state[p]

                # State initialization
                if len(state) == 0:
                    state['step'] = 0
                    state['exp_avg'] = torch.zeros_like(p.data)
                    state['exp_avg_sq'] = torch.zeros_like(p.data)

                exp_avg, exp_avg_sq = state['exp_avg'], state['exp_avg_sq']
                beta1, beta2 = group['betas']

                exp_avg_sq.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)
                exp_avg.mul_(beta1).add_(grad, alpha=1 - beta1)

                state['step'] += 1

                # Decay the first and second moment running average coefficient
                buffered = torch.tensor_buffered(state['step'])

                # Calculate the bias-corrected first moment estimate
                bias_correction1 = 1 - beta1 ** buffered
                bias_correction2 = 1 - beta2 ** buffered

                exp_avg_hat = exp_avg / bias_correction1
                exp_avg_sq_hat = exp_avg_sq / bias_correction2

                # Calculate the length of the updated vector
                r = exp_avg_sq_hat.sqrt().add_(group['eps'])
                r_hat = r

                # Length of the average
                rho_inf = (2 / (1 - beta2)) - 1
                if state['step'] > 0:
                    rho_t = rho_inf - 2 * buffered * beta2 ** buffered / (1 - beta2 ** buffered)
                else:
                    rho_t = rho_inf

                # Compute the trust ratio
                if rho_t > 4:
                    r_hat = torch.tensor(0.0)
                else:
                    r_hat = torch.min(r_hat, torch.tensor(rho_t / (buffered + 1)))

                # Compute the adaptive learning rate
                r_t = r_hat / (1 - beta2 ** (buffered + 1))

                # Update parameters
                if group['degenerated_to_sgd'] and state['step'] < 2 ** 4:
                    # Degenerate to SGD
                    p.data.add_(exp_avg_hat, alpha=-group['lr'])
                else:
                    p.data.addcdiv_(exp_avg_hat, r_t, value=-group['lr'])

        return loss


class OptimizerFactory:
    """Factory for creating optimizers with common configurations."""

    @staticmethod
    def create_optimizer(
        model: nn.Module,
        optimizer_name: str = "adam",
        lr: float = 0.001,
        weight_decay: float = 0.01,
        **kwargs,
    ) -> optim.Optimizer:
        """
        Create an optimizer for the given model.

        Args:
            model: PyTorch model.
            optimizer_name: Name of the optimizer ('adam', 'sgd', 'adamw', 'radam', 'sgdw').
            lr: Learning rate.
            weight_decay: Weight decay coefficient.
            **kwargs: Additional arguments for the optimizer.

        Returns:
            Optimizer instance.
        """
        optimizer_name = optimizer_name.lower()

        if optimizer_name == "adam":
            return optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay, **kwargs)
        elif optimizer_name == "sgd":
            return optim.SGD(model.parameters(), lr=lr, weight_decay=weight_decay, **kwargs)
        elif optimizer_name == "adamw":
            return AdamW(model.parameters(), lr=lr, weight_decay=weight_decay, **kwargs)
        elif optimizer_name == "radam":
            return RAdam(model.parameters(), lr=lr, weight_decay=weight_decay, **kwargs)
        elif optimizer_name == "sgdw":
            return SGDW(model.parameters(), lr=lr, weight_decay=weight_decay, **kwargs)
        else:
            raise ValueError(f"Unknown optimizer: {optimizer_name}")
