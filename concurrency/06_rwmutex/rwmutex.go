package rwmutex

import (
	"primitives/internal/futex"
	"sync/atomic"
)

const (
	writer     = 1 << 31       // работает писатель
	writerAtt  = 1 << 30       // писатель ждет, новых читателей не пускаем
	readersCnt = writerAtt - 1 // младшие 30 бит счетчик читателей
)

type RWMutex struct {
	state   uint32
	waiters int32 // будим только когда есть кого будить
}

func (rw *RWMutex) RLock() {
	for {
		state := atomic.LoadUint32(&rw.state)
		if state&(writer|writerAtt) != 0 {
			atomic.AddInt32(&rw.waiters, 1)
			// Wait не даст уснуть, если значение уже поменялось
			futex.Wait(&rw.state, state)
			atomic.AddInt32(&rw.waiters, -1)
			continue
		}
		if atomic.CompareAndSwapUint32(&rw.state, state, state+1) {
			return
		}
	}
}

func (rw *RWMutex) RUnlock() {
	// CAS-цикл без уступок: состояние читаем заново, а не спим
	for {
		state := atomic.LoadUint32(&rw.state)
		if state&writer != 0 || state&readersCnt == 0 {
			panic("rwmutex: RUnlock без RLock")
		}
		if state&readersCnt == 1 {
			// последний читатель: снимаем счетчик, пометку писателя не трогаем
			if atomic.CompareAndSwapUint32(&rw.state, state, state&writerAtt) {
				// если был ждущий (писатель или читатели под writerAtt) - будим
				if state&writerAtt != 0 && atomic.LoadInt32(&rw.waiters) != 0 {
					futex.WakeAll(&rw.state)
				}
				return
			}
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
			// занимаем очередь: читатели теперь ждать
			atomic.CompareAndSwapUint32(&rw.state, state, state|writerAtt)
		} else if state == writerAtt {
			// пометка наша и никого нет, забираем
			if atomic.CompareAndSwapUint32(&rw.state, writerAtt, writer) {
				return
			}
		} else {
			// читатели еще выходят или другой писатель работает, спим до отработки
			atomic.AddInt32(&rw.waiters, 1)
			futex.Wait(&rw.state, state)
			atomic.AddInt32(&rw.waiters, -1)
		}
	}
}

func (rw *RWMutex) Unlock() {
	// CAS-цикл: проверяем бит writer и только потом сбрасываем, иначе
	// ошибочный Unlock испортил бы счетчик читателей до паники
	for {
		state := atomic.LoadUint32(&rw.state)
		if state&writer == 0 {
			panic("rwmutex: Unlock без Lock")
		}
		// пометку ждущего писателя сохраняем, иначе читатели проскочат
		// вперед и потеряется приоритет писателя
		next := state & writerAtt
		if atomic.CompareAndSwapUint32(&rw.state, state, next) {
			if atomic.LoadInt32(&rw.waiters) != 0 {
				// ждали писателя - будим одного, читателей они будят сами
				futex.WakeAll(&rw.state)
			}
			return
		}
	}
}
