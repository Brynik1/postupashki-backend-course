package rwmutex

import (
	"primitives/internal/futex"
	"runtime"
	"sync/atomic"
)

const (
	writer     = 1 << 31       // работает писатель
	writerAtt  = 1 << 30       // писатель ждет, новых читателей не пускаем
	readersCnt = writerAtt - 1 // младшие 30 бит счетчик читателей
)

type RWMutex struct {
	state uint32
}

func (rw *RWMutex) RLock() {
	for {
		state := atomic.LoadUint32(&rw.state)
		if state&(writer|writerAtt) != 0 {
			futex.Wait(&rw.state, state)
			continue
		}
		if atomic.CompareAndSwapUint32(&rw.state, state, state+1) {
			return
		}
	}
}

func (rw *RWMutex) RUnlock() {
	for {
		state := atomic.LoadUint32(&rw.state)
		if state&writer != 0 || state&readersCnt == 0 {
			panic("rwmutex: RUnlock без RLock")
		}
		if state&readersCnt == 1 {
			if atomic.CompareAndSwapUint32(&rw.state, state, state&writerAtt) {
				futex.WakeAll(&rw.state)
				return
			}
			runtime.Gosched()
			continue
		}
		if atomic.CompareAndSwapUint32(&rw.state, state, state-1) {
			return
		}
	}
}

func (rw *RWMutex) Lock() {
	for {
		state := atomic.LoadUint32(&rw.state)
		if state&writerAtt == 0 {
			// Сначала занимаем очередь, читатели теперь ждать
			if atomic.CompareAndSwapUint32(&rw.state, state, state|writerAtt) {
				continue
			}
			continue
		}
		if state == writerAtt {
			// Читателей и писателей нет, забираем
			if atomic.CompareAndSwapUint32(&rw.state, writerAtt, writer) {
				return
			}
			continue
		}
		futex.Wait(&rw.state, state)
	}
}

func (rw *RWMutex) Unlock() {
	old := atomic.SwapUint32(&rw.state, 0)
	// Может быть писатель на нас еще и пометку поставил, поэтому бит а не равно
	if old&writer == 0 {
		panic("rwmutex: Unlock без Lock")
	}
	futex.WakeAll(&rw.state)
}
