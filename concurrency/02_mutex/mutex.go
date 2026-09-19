package mutex

import (
	"primitives/internal/futex"
	"sync/atomic"
)

const (
	free = iota
	held
	contended // Замок занят и есть ждущие, будем будить при Unlock
)

type Mutex struct {
	state uint32
}

func (m *Mutex) Lock() {
	if atomic.CompareAndSwapUint32(&m.state, free, held) {
		return
	}
	for {
		state := atomic.LoadUint32(&m.state)
		switch state {
		case free:
			// Берем как contended, раз ждущие уже есть
			if atomic.CompareAndSwapUint32(&m.state, free, contended) {
				return
			}
		case held:
			if atomic.CompareAndSwapUint32(&m.state, held, contended) {
				futex.Wait(&m.state, contended)
			}
			// Кас не прошел, значение поменялось, читаем заново
		default:
			// Спим только на contended: замок есть у кого-то и он разбудит,
			// если значение уже поменялось то Wait не даст уснуть
			futex.Wait(&m.state, contended)
		}
	}
}

func (m *Mutex) TryLock() bool {
	return atomic.CompareAndSwapUint32(&m.state, free, held)
}

func (m *Mutex) Unlock() {
	old := atomic.SwapUint32(&m.state, free)
	if old == free {
		panic("mutex: Unlock без Lock")
	}
	if old == contended {
		futex.Wake(&m.state)
	}
}
