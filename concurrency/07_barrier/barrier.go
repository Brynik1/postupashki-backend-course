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
	if n <= 0 {
		panic("barrier: неположительное число участников")
	}
	return &Barrier{need: uint32(n)}
}

func (b *Barrier) Wait() {
	// Запоминаем раунд, будем ждать смену раунда (а не ноль)
	round := atomic.LoadUint32(&b.round)
	// одним инкрементом вместо CAS-цикла: кто получил need - тот последний
	n := atomic.AddUint32(&b.arrived, 1)
	if n == b.need {
		// Обычный Store безопасен: пока round не сменился, участники
		// следующего раунда физически не могут прийти
		atomic.StoreUint32(&b.arrived, 0)
		atomic.AddUint32(&b.round, 1)
		futex.WakeAll(&b.round)
		return
	}
	for atomic.LoadUint32(&b.round) == round {
		futex.Wait(&b.round, round)
	}
}
