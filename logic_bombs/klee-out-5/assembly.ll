; ModuleID = 'original_prefix.bc'
source_filename = "orig_minimal_prefix.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@reached_NL = dso_local global i32 0, align 4, !dbg !0
@.str = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.1 = private unnamed_addr constant [22 x i8] c"orig_minimal_prefix.c\00", align 1
@__PRETTY_FUNCTION__.logic_bomb = private unnamed_addr constant [23 x i8] c"int logic_bomb(char *)\00", align 1
@.str.2 = private unnamed_addr constant [2 x i8] c"s\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @logic_bomb(i8* %s) #0 !dbg !13 {
entry:
  %retval = alloca i32, align 4
  %s.addr = alloca i8*, align 8
  %d = alloca double, align 8
  %symvar = alloca i32, align 4
  %d2 = alloca double, align 8
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !18, metadata !DIExpression()), !dbg !19
  call void @llvm.dbg.declare(metadata double* %d, metadata !20, metadata !DIExpression()), !dbg !22
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !23, metadata !DIExpression()), !dbg !24
  %0 = load i8*, i8** %s.addr, align 8, !dbg !25
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !25
  %1 = load i8, i8* %arrayidx, align 1, !dbg !25
  %conv = sext i8 %1 to i32, !dbg !25
  %sub = sub nsw i32 %conv, 48, !dbg !26
  store i32 %sub, i32* %symvar, align 4, !dbg !24
  %2 = load i32, i32* %symvar, align 4, !dbg !27
  %cmp = icmp sle i32 %2, 0, !dbg !29
  br i1 %cmp, label %if.then, label %if.else, !dbg !30

if.then:                                          ; preds = %entry
  store i32 1, i32* @reached_NL, align 4, !dbg !31
  call void @__assert_fail(i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0), i8* getelementptr inbounds ([22 x i8], [22 x i8]* @.str.1, i64 0, i64 0), i32 19, i8* getelementptr inbounds ([23 x i8], [23 x i8]* @__PRETTY_FUNCTION__.logic_bomb, i64 0, i64 0)) #5, !dbg !33
  unreachable, !dbg !33

if.else:                                          ; preds = %entry
  %3 = load i8*, i8** %s.addr, align 8, !dbg !34
  %arrayidx3 = getelementptr inbounds i8, i8* %3, i64 0, !dbg !34
  %4 = load i8, i8* %arrayidx3, align 1, !dbg !34
  %conv4 = sext i8 %4 to i32, !dbg !34
  %sub5 = sub nsw i32 %conv4, 48, !dbg !36
  %conv6 = sitofp i32 %sub5 to double, !dbg !34
  store double %conv6, double* %d, align 8, !dbg !37
  br label %if.end

if.end:                                           ; preds = %if.else
  %5 = load double, double* %d, align 8, !dbg !38
  %cmp7 = fcmp olt double 2.000000e+00, %5, !dbg !40
  br i1 %cmp7, label %land.lhs.true, label %if.else12, !dbg !41

land.lhs.true:                                    ; preds = %if.end
  %6 = load double, double* %d, align 8, !dbg !42
  %cmp9 = fcmp olt double %6, 4.000000e+00, !dbg !43
  br i1 %cmp9, label %if.then11, label %if.else12, !dbg !44

if.then11:                                        ; preds = %land.lhs.true
  store i32 1, i32* %retval, align 4, !dbg !45
  br label %return, !dbg !45

if.else12:                                        ; preds = %land.lhs.true, %if.end
  store i32 0, i32* %retval, align 4, !dbg !47
  br label %return, !dbg !47

return:                                           ; preds = %if.else12, %if.then11
  %7 = load i32, i32* %retval, align 4, !dbg !49
  ret i32 %7, !dbg !49
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

; Function Attrs: noreturn nounwind
declare dso_local void @__assert_fail(i8*, i8*, i32, i8*) #2

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 !dbg !50 {
entry:
  %retval = alloca i32, align 4
  %s = alloca [4 x i8], align 1
  store i32 0, i32* %retval, align 4
  call void @llvm.dbg.declare(metadata [4 x i8]* %s, metadata !53, metadata !DIExpression()), !dbg !57
  %arraydecay = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !58
  call void @klee_make_symbolic(i8* %arraydecay, i64 4, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.2, i64 0, i64 0)), !dbg !59
  %arrayidx = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !60
  %0 = load i8, i8* %arrayidx, align 1, !dbg !60
  %conv = sext i8 %0 to i32, !dbg !60
  %cmp = icmp sge i32 %conv, 0, !dbg !61
  %conv1 = zext i1 %cmp to i32, !dbg !61
  %conv2 = sext i32 %conv1 to i64, !dbg !60
  call void @klee_assume(i64 %conv2), !dbg !62
  %arraydecay3 = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !63
  %call = call i32 @logic_bomb(i8* %arraydecay3), !dbg !64
  %1 = load i32, i32* @reached_NL, align 4, !dbg !65
  %tobool = icmp ne i32 %1, 0, !dbg !65
  br i1 %tobool, label %if.end, label %if.then, !dbg !67

if.then:                                          ; preds = %entry
  call void @klee_silent_exit(i32 0) #6, !dbg !68
  unreachable, !dbg !68

if.end:                                           ; preds = %entry
  ret i32 0, !dbg !69
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #3

declare dso_local void @klee_assume(i64) #3

; Function Attrs: noreturn
declare dso_local void @klee_silent_exit(i32) #4

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { noreturn nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { noreturn "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #5 = { noreturn nounwind }
attributes #6 = { noreturn }

!llvm.dbg.cu = !{!2}
!llvm.module.flags = !{!7, !8, !9, !10, !11}
!llvm.ident = !{!12}

!0 = !DIGlobalVariableExpression(var: !1, expr: !DIExpression())
!1 = distinct !DIGlobalVariable(name: "reached_NL", scope: !2, file: !3, line: 9, type: !6, isLocal: false, isDefinition: true)
!2 = distinct !DICompileUnit(language: DW_LANG_C99, file: !3, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !4, globals: !5, splitDebugInlining: false, nameTableKind: None)
!3 = !DIFile(filename: "orig_minimal_prefix.c", directory: "/home/klee")
!4 = !{}
!5 = !{!0}
!6 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!7 = !{i32 7, !"Dwarf Version", i32 4}
!8 = !{i32 2, !"Debug Info Version", i32 3}
!9 = !{i32 1, !"wchar_size", i32 4}
!10 = !{i32 7, !"uwtable", i32 1}
!11 = !{i32 7, !"frame-pointer", i32 2}
!12 = !{!"clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)"}
!13 = distinct !DISubprogram(name: "logic_bomb", scope: !3, file: !3, line: 12, type: !14, scopeLine: 12, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!14 = !DISubroutineType(types: !15)
!15 = !{!6, !16}
!16 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !17, size: 64)
!17 = !DIBasicType(name: "char", size: 8, encoding: DW_ATE_signed_char)
!18 = !DILocalVariable(name: "s", arg: 1, scope: !13, file: !3, line: 12, type: !16)
!19 = !DILocation(line: 12, column: 22, scope: !13)
!20 = !DILocalVariable(name: "d", scope: !13, file: !3, line: 13, type: !21)
!21 = !DIBasicType(name: "double", size: 64, encoding: DW_ATE_float)
!22 = !DILocation(line: 13, column: 12, scope: !13)
!23 = !DILocalVariable(name: "symvar", scope: !13, file: !3, line: 15, type: !6)
!24 = !DILocation(line: 15, column: 9, scope: !13)
!25 = !DILocation(line: 15, column: 18, scope: !13)
!26 = !DILocation(line: 15, column: 23, scope: !13)
!27 = !DILocation(line: 16, column: 10, scope: !28)
!28 = distinct !DILexicalBlock(scope: !13, file: !3, line: 16, column: 10)
!29 = !DILocation(line: 16, column: 17, scope: !28)
!30 = !DILocation(line: 16, column: 10, scope: !13)
!31 = !DILocation(line: 18, column: 16, scope: !32)
!32 = distinct !DILexicalBlock(scope: !28, file: !3, line: 16, column: 23)
!33 = !DILocation(line: 19, column: 5, scope: !32)
!34 = !DILocation(line: 23, column: 13, scope: !35)
!35 = distinct !DILexicalBlock(scope: !28, file: !3, line: 22, column: 12)
!36 = !DILocation(line: 23, column: 18, scope: !35)
!37 = !DILocation(line: 23, column: 11, scope: !35)
!38 = !DILocation(line: 25, column: 12, scope: !39)
!39 = distinct !DILexicalBlock(scope: !13, file: !3, line: 25, column: 8)
!40 = !DILocation(line: 25, column: 10, scope: !39)
!41 = !DILocation(line: 25, column: 14, scope: !39)
!42 = !DILocation(line: 25, column: 17, scope: !39)
!43 = !DILocation(line: 25, column: 19, scope: !39)
!44 = !DILocation(line: 25, column: 8, scope: !13)
!45 = !DILocation(line: 26, column: 9, scope: !46)
!46 = distinct !DILexicalBlock(scope: !39, file: !3, line: 25, column: 23)
!47 = !DILocation(line: 28, column: 9, scope: !48)
!48 = distinct !DILexicalBlock(scope: !39, file: !3, line: 27, column: 10)
!49 = !DILocation(line: 30, column: 1, scope: !13)
!50 = distinct !DISubprogram(name: "main", scope: !3, file: !3, line: 32, type: !51, scopeLine: 32, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!51 = !DISubroutineType(types: !52)
!52 = !{!6}
!53 = !DILocalVariable(name: "s", scope: !50, file: !3, line: 33, type: !54)
!54 = !DICompositeType(tag: DW_TAG_array_type, baseType: !17, size: 32, elements: !55)
!55 = !{!56}
!56 = !DISubrange(count: 4)
!57 = !DILocation(line: 33, column: 10, scope: !50)
!58 = !DILocation(line: 34, column: 24, scope: !50)
!59 = !DILocation(line: 34, column: 5, scope: !50)
!60 = !DILocation(line: 36, column: 17, scope: !50)
!61 = !DILocation(line: 36, column: 22, scope: !50)
!62 = !DILocation(line: 36, column: 5, scope: !50)
!63 = !DILocation(line: 37, column: 16, scope: !50)
!64 = !DILocation(line: 37, column: 5, scope: !50)
!65 = !DILocation(line: 38, column: 10, scope: !66)
!66 = distinct !DILexicalBlock(scope: !50, file: !3, line: 38, column: 9)
!67 = !DILocation(line: 38, column: 9, scope: !50)
!68 = !DILocation(line: 38, column: 22, scope: !66)
!69 = !DILocation(line: 39, column: 5, scope: !50)
