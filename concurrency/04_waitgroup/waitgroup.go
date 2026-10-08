package waitgroup

import (
	"primitives/internal/futex"
	"sync/atomic"
)

type WaitGroup struct {
	count   uint32
	waiters int32 // WakeAll зовется только когда есть кому просыпаться
}

const maxCount = 1<<31 - 1

// Add меняет счетчик одним CAS, проверки тоже без нарушения данных:
// при уходе в минус или переполнении паникуем до записи нового значения
func (wg *WaitGroup) Add(delta int) {
	for {
		count := atomic.LoadUint32(&wg.count)
		next := int64(count) + int64(delta)
		if next < 0 {
			panic("waitgroup: счетчик ушел в минус")
		}
		if next > int64(maxCount) {
			panic("waitgroup: переполнение счетчика")
		}
		if atomic.CompareAndSwapUint32(&wg.count, count, uint32(next)) {
			// обнулили и кто-то еще спит в Wait - будим всех
			if next == 0 && count != 0 && atomic.LoadInt32(&wg.waiters) != 0 {
				futex.WakeAll(&wg.count)
			}
			return
		}
	}
}

// Done это просто Add(-1)
func (wg *WaitGroup) Done() {
	wg.Add(-1)
}

func (wg *WaitGroup) Wait() {
	for {
		count := atomic.LoadUint32(&wg.count)
		if count == 0 {
			return
		}
		atomic.AddInt32(&wg.waiters, 1)
		// перепроверка под зарегистрированным ожиданием: обнуление могли
		// случиться раньше, чем мы встали в waiters, и WakeAll нас не поймал
		if atomic.LoadUint32(&wg.count) == 0 {
			atomic.AddInt32(&wg.waiters, -1)
			return
		}
		// Если было уже не это значение, то будильник уже сработал
		futex.Wait(&wg.count, count)
		atomic.AddInt32(&wg.waiters, -1)
	}
}
