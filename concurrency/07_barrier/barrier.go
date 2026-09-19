package barrier

import (
	"primitives/internal/futex"
	"sync/atomic"
)

type Barrier struct {
	need    uint32
	arrived uint32
	round   uint32
}

func New(n int) *Barrier {
	return &Barrier{need: uint32(n)}
}

func (b *Barrier) Wait() {
	// Запоминаем раунд, будем ждать смену раунда (а не ноль)
	round := atomic.LoadUint32(&b.round)
	for {
		arrived := atomic.LoadUint32(&b.arrived)
		if arrived+1 == b.need {
			if atomic.CompareAndSwapUint32(&b.arrived, arrived, 0) {
				atomic.AddUint32(&b.round, 1)
				futex.WakeAll(&b.round)
				return
			}
			continue
		}
		if atomic.CompareAndSwapUint32(&b.arrived, arrived, arrived+1) {
			break
		}
	}
	for atomic.LoadUint32(&b.round) == round {
		futex.Wait(&b.round, round)
	}
}
