section .data
    ; сообщения об ошибках и служебные символы
    err_corrupt db ": файл испорчен", 10   ; 10 = код переноса строки '\n'
    err_corrupt_len equ $ - err_corrupt     ; вычисление длины строки в байтах

    colon_space db ": "                     ; разделитель формата вывода
    colon_space_len equ $ - colon_space     ; длина разделителя (2 байта)

    newline db 10                           ; символ перевода строки '\n'

section .bss
    ; буферы и переменные в оперативной памяти
    BUFFER_SIZE equ 16384                   ; константа максимального размера файла (16 кб)
    file_buffer resb BUFFER_SIZE            ; буфер для считывания содержимого файла
    num_buffer resb 32                      ; буфер для формирования строки числа при выводе
    filename_ptr resq 1                     ; указатель на строку с именем входного файла (argv[1])
    sum_x resq 1                            ; накопленная сумма элементов массива x
    count_x resq 1                          ; количество элементов массива x
    sum_y resq 1                            ; накопленная сумма элементов массива y
    count_y resq 1                          ; количество элементов массива y

section .text
    global _start

_start:
    ; --- проверка аргументов командной строки ---
    mov rax, [rsp]                          ; [rsp] = argc (количество переданных аргументов)
    cmp rax, 2                              ; требуется минимум 2: имя программы и имя файла
    jl .fatal_no_file                       ; если аргументов меньше 2, завершаем процесс

    mov rax, [rsp + 16]                     ; [rsp + 16] = argv[1] (указатель на имя файла)
    mov [filename_ptr], rax                 ; сохраняем указатель на имя файла в память

    ; --- системный вызов sys_open ---
    mov rax, 2                              ; номер системного вызова sys_open
    mov rdi, [filename_ptr]                 ; первый аргумент: путь к файлу
    mov rsi, 0                              ; второй аргумент: флаг O_RDONLY (только чтение)
    mov rdx, 0                              ; третий аргумент: права доступа (mode)
    syscall                                 ; вызов ядра linux

    cmp rax, 0                              ; проверка возвращаемого значения
    jl .file_error                          ; отрицательное значение означает ошибку открытия
    mov r12, rax                            ; сохраняем файловый дескриптор в защищенный регистр r12

    ; --- системный вызов sys_read ---
    mov rax, 0                              ; номер системного вызова sys_read
    mov rdi, r12                            ; дескриптор открытого файла
    mov rsi, file_buffer                    ; адрес буфера-приемника
    mov rdx, BUFFER_SIZE                    ; максимальное количество считываемых байт
    syscall

    cmp rax, 0                              ; проверка количества прочитанных байт
    jle .file_error_close                   ; если прочитано <= 0 байт — файл пустой или сбой
    mov r13, rax                            ; сохраняем фактическое число прочитанных байт

    ; --- системный вызов sys_close ---
    mov rax, 3                              ; номер системного вызова sys_close
    mov rdi, r12                            ; дескриптор закрываемого файла
    syscall

    ; установка символа в конец прочитанных данных
    mov byte [file_buffer + r13], 0

    ; --- парсинг строк---
    lea rsi, [file_buffer]                  ; rsi = указатель на начало буфера файла
    call parse_line                         ; разбор строки с числами
    cmp rax, 0                              ; проверка статуса выполнения функции
    je .file_error                          ; rax == 0 сигнализирует об ошибке формата

    mov [sum_x], rbx                        ; сохраняем сумму массива x (возвращена в rbx)
    mov [count_x], rcx                      ; сохраняем количество элементов x (возвращено в rcx)

    call parse_line                         ; rsi уже смещен на начало второй строки
    cmp rax, 0
    je .file_error

    mov [sum_y], rbx                        ; сохраняем сумму массива y
    mov [count_y], rcx                      ; сохраняем количество элементов y

    ; --- валидация входных данных по условию задачи ---
    mov rax, [count_x]                      ; загружаем размерность массива x
    cmp rax, 0                              ; количество элементов должно быть строго > 0
    jle .file_error
    cmp rax, [count_y]                      ; размеры массивов обязаны совпадать: count_x == count_y
    jne .file_error

    ; проверка отсутствия лишних данных после второй строки
.check_trailing:
    mov al, [rsi]                           ; читаем очередной символ
    cmp al, 0                               ; достигнут корректный конец файла
    je .calculate
    cmp al, ' '                             ; пропуск допустимых пробелов
    je .skip_tr
    cmp al, 10                              ; пропуск допустимого переноса строки '\n'
    je .skip_tr
    cmp al, 13                              ; пропуск допустимого возврата каретки '\r'
    je .skip_tr
    jmp .file_error                         ; наличие других символов означает некорректный формат
.skip_tr:
    inc rsi                                 ; смещение к следующему символу
    jmp .check_trailing

    ; --- вычисление среднего арифметического разностей ---
.calculate:
    ; формула: average = (sum_x - sum_y) / count_x
    mov rax, [sum_x]                        ; rax = общая сумма x
    sub rax, [sum_y]                        ; rax = sum_x - sum_y
    mov rbx, [count_x]                      ; rbx = n (делитель)

    cqo                                     ; расширение знака rax в rdx:rax для знакового деления
    idiv rbx                                ; знаковое деление 128-битного rdx:rax на rbx
    mov r14, rax                            ; сохраняем результат частного в r14

    ; --- формирование вывода ---
    mov rdi, [filename_ptr]                 ; первый аргумент: указатель на имя файла
    call print_cstring                      ; вывод имени файла

    mov rax, 1                              ; sys_write
    mov rdi, 1                              ; дескриптор stdout
    mov rsi, colon_space                    ; адрес строки ": "
    mov rdx, colon_space_len                ; длина строки
    syscall

    mov rdi, r14                            ; первый аргумент: вычисленный результат
    call print_int                          ; вывод знакового целого числа в терминал

    mov rax, 1                              ; sys_write
    mov rdi, 1                              ; дескриптор stdout
    mov rsi, newline                        ; адрес символа '\n'
    mov rdx, 1                              ; длина (1 байт)
    syscall

    ; успешный выход из программы
    mov rax, 60                             ; номер системного вызова sys_exit
    xor rdi, rdi                            ; код возврата 0 (успешное завершение)
    syscall

    ; --- обработка ошибок ---
.file_error_close:
    mov rax, 3                              ; sys_close
    mov rdi, r12                            ; закрываем дескриптор открытого файла
    syscall

.file_error:
    mov rdi, [filename_ptr]                 ; вывод имени файла
    call print_cstring

    mov rax, 1                              ; sys_write
    mov rdi, 1                              ; stdout
    mov rsi, err_corrupt                    ; сообщение об ошибке
    mov rdx, err_corrupt_len
    syscall

    mov rax, 60                             ; sys_exit
    mov rdi, 1                              ; код возврата 1 (ошибка выполнения)
    syscall

.fatal_no_file:
    mov rax, 60                             ; sys_exit
    mov rdi, 1                              ; код возврата 1
    syscall


; ==============================================================================
; parse_line
; назначение: посимвольный разбор строки чисел, разделенных запятыми
; вход:   rsi — указатель на текущую позицию в буфере текста
; выход:  rax — статус выполнения (1 — успешно, 0 — ошибка формата)
;         rbx — сумма чисел в разобранной строке
;         rcx — количество распознанных чисел
;         rsi — указатель смещается за символ переноса строки '\n'
; ==============================================================================
parse_line:
    push rbp                                ; сохранение базового указателя стека
    mov rbp, rsp                            ; установка нового стекового кадра
    xor rbx, rbx                            ; rbx = 0 (накопитель суммы)
    xor rcx, rcx                            ; rcx = 0 (счетчик элементов)

.skip_spaces_before_num:
    mov al, [rsi]                           ; чтение текущего символа
    cmp al, ' '                             ; пропуск ведущих пробелов
    je .inc_and_skip
    cmp al, 9                               ; пропуск символов горизонтальной табуляции '\t'
    je .inc_and_skip
    jmp .check_sign
.inc_and_skip:
    inc rsi                                 ; смещение указателя буфера вперед
    jmp .skip_spaces_before_num

.check_sign:
    mov al, [rsi]
    cmp al, 10                              ; проверка на пустую строку до первого числа
    je .line_end_check
    cmp al, 0                               ; проверка на преждевременный конец файла
    je .line_end_check

    xor r8, r8                              ; r8 = 0 (флаг знака: 0 — положительное, 1 — отрицательное)
    cmp al, '-'                             ; проверка на наличие знака минус
    jne .parse_digits
    mov r8, 1                               ; установка флага отрицательного числа
    inc rsi                                 ; пропуск символа минуса
    mov al, [rsi]                           ; чтение первого символа после знака

.parse_digits:
    cmp al, '0'                             ; символ обязан быть в диапазоне 0..9
    jl .parse_fail
    cmp al, '9'
    jg .parse_fail

    xor r9, r9                              ; r9 = 0 (аккумулятор текущего числа)
.digit_loop:
    sub al, '0'                             ; преобразование ascii-кода символа в цифру (0..9)
    movzx rax, al                           ; расширение байта al нулями до 64 бит в rax
    imul r9, r9, 10                         ; сдвиг десятичного разряда: r9 = r9 * 10
    add r9, rax                             ; добавление очередной цифры: r9 = r9 + цифра

    inc rsi                                 ; переход к следующему символу
    mov al, [rsi]                           ; чтение следующего символа
    cmp al, '0'                             ; проверка продолжения цифрового блока
    jl .finish_number
    cmp al, '9'
    jle .digit_loop

.finish_number:
    cmp r8, 1                               ; проверка флага отрицательного числа
    jne .add_to_sum
    neg r9                                  ; инверсия знака числа: r9 = -r9

.add_to_sum:
    add rbx, r9                             ; добавление числа к общей сумме строки
    inc rcx                                 ; увеличение количества распознанных чисел

    ; пропуск завершающих пробелов после числа перед разделителем
.skip_spaces_after_num:
    mov al, [rsi]
    cmp al, ' '
    je .inc_sp
    cmp al, 9
    je .inc_sp
    jmp .check_delimeter
.inc_sp:
    inc rsi
    jmp .skip_spaces_after_num

.check_delimeter:
    mov al, [rsi]
    cmp al, ','                             ; наличие запятой означает переход к следующему числу
    je .has_comma
    cmp al, 13                              ; проверка конца строки (windows-формат '\r')
    je .is_newline
    cmp al, 10                              ; проверка конца строки (unix-формат '\n')
    je .is_newline
    cmp al, 0                               ; проверка конца файла
    je .is_newline
    jmp .parse_fail                         ; некорректный символ-разделитель

.has_comma:
    inc rsi                                 ; пропуск запятой
    jmp .skip_spaces_before_num             ; переход к чтению следующего числа

.is_newline:
    cmp byte [rsi], 13                      ; пропуск символа '\r', если он присутствует
    jne .check_nl
    inc rsi
.check_nl:
    cmp byte [rsi], 10                      ; пропуск завершающего символа '\n'
    jne .line_done
    inc rsi

.line_done:
    cmp rcx, 0                              ; строка не должна быть пустой
    jle .parse_fail
    mov rax, 1                              ; rax = 1 (код успешного завершения разбора)
    mov rsp, rbp                            ; восстановление стека
    pop rbp                                 ; восстановление базового указателя
    ret

.line_end_check:
    jmp .parse_fail

.parse_fail:
    xor rax, rax                            ; rax = 0 (код ошибки разбора)
    mov rsp, rbp
    pop rbp
    ret


; ==============================================================================
; print_cstring
; назначение: вывод строки с 0 в стандартный поток вывода
; вход:   rdi — адрес начала строки с 0
; ==============================================================================
print_cstring:
    push rbx                                ; сохранение содержимого вызываемого регистра
    mov rbx, rdi                            ; rbx = базовый адрес строки
    xor rdx, rdx                            ; rdx = 0 (счетчик длины строки)
.len_loop:
    cmp byte [rbx + rdx], 0                 ; поиск 0
    je .do_print
    inc rdx                                 ; увеличение счетчика длины
    jmp .len_loop
.do_print:
    mov rax, 1                              ; номер вызова sys_write
    mov rsi, rbx                            ; адрес выводимого буфера
    mov rdi, 1                              ; дескриптор stdout
    syscall
    pop rbx                                 ; восстановление регистра rbx
    ret


; ==============================================================================
; print_int
; назначение: преобразование 64-битного целого числа со знаком в строку и вывод
; вход:   rdi — 64-битное целое число со знаком
; ==============================================================================
print_int:
    push rbx                                ; сохранение регистра rbx
    mov rax, rdi                            ; rax = делимое (выводимое число)
    lea rsi, [num_buffer + 30]              ; установка указателя в конец буфера
    mov byte [rsi], 0                       ; 0

    test rax, rax                           ; проверка знака числа
    jns .convert_loop                       ; если число положительное, переходим к делению
    neg rax                                 ; делаем число положительным: rax = -rax
    mov r8, 1                               ; r8 = 1 (флаг необходимости вывода знака минус)
    jmp .convert_loop_start

.convert_loop:
    xor r8, r8                              ; r8 = 0 (число положительное)
.convert_loop_start:
    mov rbx, 10                             ; rbx = 10 (делитель для десятичной системы)
.digits:
    xor rdx, rdx                            ; очистка rdx перед беззнаковым делением
    div rbx                                 ; беззнаковое деление rax на 10: rax = частное, rdx = остаток
    add dl, '0'                             ; преобразование остатка в ascii-символ
    dec rsi                                 ; смещение указателя буфера влево
    mov [rsi], dl                           ; запись символа цифры
    test rax, rax                           ; проверка, остались ли еще цифры
    jnz .digits

    cmp r8, 1                               ; проверка необходимости вывода минуса
    jne .print_now
    dec rsi
    mov byte [rsi], '-'                     ; добавление символа "-" перед старшей цифрой

.print_now:
    lea rdx, [num_buffer + 30]              ; rdx = адрес конца сформированной строки
    sub rdx, rsi                            ; rdx = длина строки (разность адресов конца и начала)

    mov rax, 1                              ; sys_write
    mov rdi, 1                              ; stdout
    syscall

    pop rbx                                 ; восстановление rbx
    ret