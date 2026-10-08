package mutex

import (
	"primitives/internal/futex"
	"runtime"
	"sync/atomic"
)

const (
	free = iota
	held
	contended // Замок занят и есть ждущие, будем будить при Unlock
)

// короткий спин перед переходом в ядро: на коротких критических
// секциях экономит системные вызовы
const spinBeforeSleep = 32

type Mutex struct {
	state uint32
}

func (m *Mutex) Lock() {
	// быстрый путь
	if atomic.CompareAndSwapUint32(&m.state, free, held) {
		return
	}
	// спин: пробуем забрать без засыпания, только с уступкой планировщика
	for i := 0; i < spinBeforeSleep; i++ {
		if atomic.CompareAndSwapUint32(&m.state, free, held) {
			return
		}
		runtime.Gosched()
	}
	// медленный путь: Swap одновременно помечает, что есть ждущие, и забирает
	// лок, если он освободился; спим на contended - владелец разбудит
	for {
		if atomic.SwapUint32(&m.state, contended) == free {
			return
		}
		futex.Wait(&m.state, contended)
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
