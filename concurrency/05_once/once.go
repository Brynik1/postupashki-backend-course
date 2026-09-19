package once

import (
	"primitives/internal/futex"
	"sync/atomic"
)

const (
	idle    = iota // еще не начинали
	running        // кто-то выполняет f, остальные ждут
	done           // готово, больше не запускаем
)

type Once struct {
	state uint32
}

func (o *Once) Do(f func()) {
	for {
		state := atomic.LoadUint32(&o.state)
		switch state {
		case done:
			return
		case running:
			// Ждем пока первый закончит, чтобы вернуться после готового результата
			futex.Wait(&o.state, running)
		default:
			if atomic.CompareAndSwapUint32(&o.state, idle, running) {
				defer func() {
					// Даже если f паникует считаем работу сделанной,
					// перезапускать на полуготовом состоянии нельзя
					atomic.StoreUint32(&o.state, done)
					futex.WakeAll(&o.state)
				}()
				f()
				return
			}
		}
	}
}

func (o *Once) Done() bool {
	return atomic.LoadUint32(&o.state) == done
}
