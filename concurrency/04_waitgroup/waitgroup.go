package waitgroup

import (
	"primitives/internal/futex"
	"sync/atomic"
)

type WaitGroup struct {
	count uint32
}

func (wg *WaitGroup) Add(delta int) {
	if delta >= 0 {
		atomic.AddUint32(&wg.count, uint32(delta))
	} else {
		for i := 0; i < -delta; i++ {
			wg.Done()
		}
	}
}

func (wg *WaitGroup) Done() {
	for {
		count := atomic.LoadUint32(&wg.count)
		if count == 0 {
			panic("waitgroup: счётчик ушёл в минус")
		}
		if atomic.CompareAndSwapUint32(&wg.count, count, count-1) {
			// Обнулили, все ждущие могут идти
			if count == 1 {
				futex.WakeAll(&wg.count)
			}
			return
		}
	}
}

func (wg *WaitGroup) Wait() {
	for {
		count := atomic.LoadUint32(&wg.count)
		if count == 0 {
			return
		}
		// Если было уже не это значение, то будильник уже сработал
		futex.Wait(&wg.count, count)
	}
}
