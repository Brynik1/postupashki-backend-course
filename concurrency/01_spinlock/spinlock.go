package spinlock

import (
	"runtime"
	"sync/atomic"
)

type Spinlock struct {
	locked atomic.Bool
}

func (s *Spinlock) Lock() {
	for {
		if s.locked.CompareAndSwap(false, true) {
			return
		}
		// Иначе можно голодать, если владелец не успеет отпустить замок
		runtime.Gosched()
	}
}

func (s *Spinlock) TryLock() bool {
	return s.locked.CompareAndSwap(false, true)
}

func (s *Spinlock) Unlock() {
	if !s.locked.CompareAndSwap(true, false) {
		panic("spinlock: Unlock без Lock")
	}
}

type TTAS struct {
	locked atomic.Bool
}

// Сначала много читаем, когда замок выглядит свободным пробуем записать
func (s *TTAS) Lock() {
	for {
		for s.locked.Load() {
			runtime.Gosched()
		}
		if s.locked.CompareAndSwap(false, true) {
			return
		}
	}
}

func (s *TTAS) TryLock() bool {
	return s.locked.CompareAndSwap(false, true)
}

func (s *TTAS) Unlock() {
	if !s.locked.CompareAndSwap(true, false) {
		panic("spinlock: Unlock без Lock")
	}
}
