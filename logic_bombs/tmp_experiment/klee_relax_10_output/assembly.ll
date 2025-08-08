; ModuleID = '/home/klee/tmp_experiment/orig_minimal_prefix_relaxed_10.bc'
source_filename = "/home/klee/tmp_experiment/orig_minimal_prefix_relaxed_10.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@reached_NL = dso_local global i32 0, align 4, !dbg !0
@.str = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.1 = private unnamed_addr constant [59 x i8] c"/home/klee/tmp_experiment/orig_minimal_prefix_relaxed_10.c\00", align 1
@__PRETTY_FUNCTION__.logic_bomb = private unnamed_addr constant [23 x i8] c"int logic_bomb(char *)\00", align 1
@.str.2 = private unnamed_addr constant [2 x i8] c"s\00", align 1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @logic_bomb(i8* %s) #0 !dbg !14 {
entry:
  %s.addr = alloca i8*, align 8
  %symvar = alloca i32, align 4
  %d = alloca double, align 8
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !19, metadata !DIExpression()), !dbg !20
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !21, metadata !DIExpression()), !dbg !22
  %0 = load i8*, i8** %s.addr, align 8, !dbg !23
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !23
  %1 = load i8, i8* %arrayidx, align 1, !dbg !23
  %conv = sext i8 %1 to i32, !dbg !23
  %sub = sub nsw i32 %conv, 48, !dbg !24
  store i32 %sub, i32* %symvar, align 4, !dbg !22
  %2 = load i8*, i8** %s.addr, align 8, !dbg !25
  %arrayidx1 = getelementptr inbounds i8, i8* %2, i64 0, !dbg !25
  %3 = load i8, i8* %arrayidx1, align 1, !dbg !25
  %conv2 = sext i8 %3 to i32, !dbg !25
  %sub3 = sub nsw i32 %conv2, 0, !dbg !26
  %conv4 = sitofp i32 %sub3 to double, !dbg !25
  %4 = call double @llvm.fabs.f64(double %conv4), !dbg !27
  %cmp = fcmp ole double %4, 1.000000e+00, !dbg !28
  %conv5 = zext i1 %cmp to i32, !dbg !28
  %conv6 = sext i32 %conv5 to i64, !dbg !27
  call void @klee_assume(i64 %conv6), !dbg !29
  %5 = load i8*, i8** %s.addr, align 8, !dbg !30
  %arrayidx7 = getelementptr inbounds i8, i8* %5, i64 1, !dbg !30
  %6 = load i8, i8* %arrayidx7, align 1, !dbg !30
  %conv8 = sext i8 %6 to i32, !dbg !30
  %sub9 = sub nsw i32 %conv8, 255, !dbg !31
  %conv10 = sitofp i32 %sub9 to double, !dbg !30
  %7 = call double @llvm.fabs.f64(double %conv10), !dbg !32
  %cmp11 = fcmp ole double %7, 2.550000e+01, !dbg !33
  %conv12 = zext i1 %cmp11 to i32, !dbg !33
  %conv13 = sext i32 %conv12 to i64, !dbg !32
  call void @klee_assume(i64 %conv13), !dbg !34
  %8 = load i8*, i8** %s.addr, align 8, !dbg !35
  %arrayidx14 = getelementptr inbounds i8, i8* %8, i64 2, !dbg !35
  %9 = load i8, i8* %arrayidx14, align 1, !dbg !35
  %conv15 = sext i8 %9 to i32, !dbg !35
  %sub16 = sub nsw i32 %conv15, 255, !dbg !36
  %conv17 = sitofp i32 %sub16 to double, !dbg !35
  %10 = call double @llvm.fabs.f64(double %conv17), !dbg !37
  %cmp18 = fcmp ole double %10, 2.550000e+01, !dbg !38
  %conv19 = zext i1 %cmp18 to i32, !dbg !38
  %conv20 = sext i32 %conv19 to i64, !dbg !37
  call void @klee_assume(i64 %conv20), !dbg !39
  %11 = load i8*, i8** %s.addr, align 8, !dbg !40
  %arrayidx21 = getelementptr inbounds i8, i8* %11, i64 3, !dbg !40
  %12 = load i8, i8* %arrayidx21, align 1, !dbg !40
  %conv22 = sext i8 %12 to i32, !dbg !40
  %sub23 = sub nsw i32 %conv22, 255, !dbg !41
  %conv24 = sitofp i32 %sub23 to double, !dbg !40
  %13 = call double @llvm.fabs.f64(double %conv24), !dbg !42
  %cmp25 = fcmp ole double %13, 2.550000e+01, !dbg !43
  %conv26 = zext i1 %cmp25 to i32, !dbg !43
  %conv27 = sext i32 %conv26 to i64, !dbg !42
  call void @klee_assume(i64 %conv27), !dbg !44
  store i32 1, i32* @reached_NL, align 4, !dbg !45
  call void @__assert_fail(i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0), i8* getelementptr inbounds ([59 x i8], [59 x i8]* @.str.1, i64 0, i64 0), i32 23, i8* getelementptr inbounds ([23 x i8], [23 x i8]* @__PRETTY_FUNCTION__.logic_bomb, i64 0, i64 0)) #5, !dbg !46
  unreachable, !dbg !46
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

declare dso_local void @klee_assume(i64) #2

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare double @llvm.fabs.f64(double) #1

; Function Attrs: noreturn nounwind
declare dso_local void @__assert_fail(i8*, i8*, i32, i8*) #3

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main() #0 !dbg !47 {
entry:
  %retval = alloca i32, align 4
  %s = alloca [4 x i8], align 1
  store i32 0, i32* %retval, align 4
  call void @llvm.dbg.declare(metadata [4 x i8]* %s, metadata !50, metadata !DIExpression()), !dbg !54
  %arraydecay = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !55
  call void @klee_make_symbolic(i8* %arraydecay, i64 4, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.2, i64 0, i64 0)), !dbg !56
  %arrayidx = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !57
  %0 = load i8, i8* %arrayidx, align 1, !dbg !57
  %conv = sext i8 %0 to i32, !dbg !57
  %cmp = icmp sge i32 %conv, 0, !dbg !58
  %conv1 = zext i1 %cmp to i32, !dbg !58
  %conv2 = sext i32 %conv1 to i64, !dbg !57
  call void @klee_assume(i64 %conv2), !dbg !59
  %arraydecay3 = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !60
  %call = call i32 @logic_bomb(i8* %arraydecay3), !dbg !61
  %1 = load i32, i32* @reached_NL, align 4, !dbg !62
  %tobool = icmp ne i32 %1, 0, !dbg !62
  br i1 %tobool, label %if.end, label %if.then, !dbg !64

if.then:                                          ; preds = %entry
  call void @klee_silent_exit(i32 0) #6, !dbg !65
  unreachable, !dbg !65

if.end:                                           ; preds = %entry
  ret i32 0, !dbg !66
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #2

; Function Attrs: noreturn
declare dso_local void @klee_silent_exit(i32) #4

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { noreturn nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { noreturn "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #5 = { noreturn nounwind }
attributes #6 = { noreturn }

!llvm.dbg.cu = !{!2}
!llvm.module.flags = !{!8, !9, !10, !11, !12}
!llvm.ident = !{!13}

!0 = !DIGlobalVariableExpression(var: !1, expr: !DIExpression())
!1 = distinct !DIGlobalVariable(name: "reached_NL", scope: !2, file: !6, line: 9, type: !7, isLocal: false, isDefinition: true)
!2 = distinct !DICompileUnit(language: DW_LANG_C99, file: !3, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !4, globals: !5, splitDebugInlining: false, nameTableKind: None)
!3 = !DIFile(filename: "/home/klee/tmp_experiment/orig_minimal_prefix_relaxed_10.c", directory: "/home/klee")
!4 = !{}
!5 = !{!0}
!6 = !DIFile(filename: "tmp_experiment/orig_minimal_prefix_relaxed_10.c", directory: "/home/klee")
!7 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!8 = !{i32 7, !"Dwarf Version", i32 4}
!9 = !{i32 2, !"Debug Info Version", i32 3}
!10 = !{i32 1, !"wchar_size", i32 4}
!11 = !{i32 7, !"uwtable", i32 1}
!12 = !{i32 7, !"frame-pointer", i32 2}
!13 = !{!"clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)"}
!14 = distinct !DISubprogram(name: "logic_bomb", scope: !6, file: !6, line: 12, type: !15, scopeLine: 12, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!15 = !DISubroutineType(types: !16)
!16 = !{!7, !17}
!17 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !18, size: 64)
!18 = !DIBasicType(name: "char", size: 8, encoding: DW_ATE_signed_char)
!19 = !DILocalVariable(name: "s", arg: 1, scope: !14, file: !6, line: 12, type: !17)
!20 = !DILocation(line: 12, column: 22, scope: !14)
!21 = !DILocalVariable(name: "symvar", scope: !14, file: !6, line: 15, type: !7)
!22 = !DILocation(line: 15, column: 9, scope: !14)
!23 = !DILocation(line: 15, column: 18, scope: !14)
!24 = !DILocation(line: 15, column: 23, scope: !14)
!25 = !DILocation(line: 17, column: 22, scope: !14)
!26 = !DILocation(line: 17, column: 27, scope: !14)
!27 = !DILocation(line: 17, column: 17, scope: !14)
!28 = !DILocation(line: 17, column: 32, scope: !14)
!29 = !DILocation(line: 17, column: 5, scope: !14)
!30 = !DILocation(line: 18, column: 22, scope: !14)
!31 = !DILocation(line: 18, column: 27, scope: !14)
!32 = !DILocation(line: 18, column: 17, scope: !14)
!33 = !DILocation(line: 18, column: 34, scope: !14)
!34 = !DILocation(line: 18, column: 5, scope: !14)
!35 = !DILocation(line: 19, column: 22, scope: !14)
!36 = !DILocation(line: 19, column: 27, scope: !14)
!37 = !DILocation(line: 19, column: 17, scope: !14)
!38 = !DILocation(line: 19, column: 34, scope: !14)
!39 = !DILocation(line: 19, column: 5, scope: !14)
!40 = !DILocation(line: 20, column: 22, scope: !14)
!41 = !DILocation(line: 20, column: 27, scope: !14)
!42 = !DILocation(line: 20, column: 17, scope: !14)
!43 = !DILocation(line: 20, column: 34, scope: !14)
!44 = !DILocation(line: 20, column: 5, scope: !14)
!45 = !DILocation(line: 22, column: 16, scope: !14)
!46 = !DILocation(line: 23, column: 5, scope: !14)
!47 = distinct !DISubprogram(name: "main", scope: !6, file: !6, line: 34, type: !48, scopeLine: 34, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!48 = !DISubroutineType(types: !49)
!49 = !{!7}
!50 = !DILocalVariable(name: "s", scope: !47, file: !6, line: 35, type: !51)
!51 = !DICompositeType(tag: DW_TAG_array_type, baseType: !18, size: 32, elements: !52)
!52 = !{!53}
!53 = !DISubrange(count: 4)
!54 = !DILocation(line: 35, column: 10, scope: !47)
!55 = !DILocation(line: 36, column: 24, scope: !47)
!56 = !DILocation(line: 36, column: 5, scope: !47)
!57 = !DILocation(line: 38, column: 17, scope: !47)
!58 = !DILocation(line: 38, column: 22, scope: !47)
!59 = !DILocation(line: 38, column: 5, scope: !47)
!60 = !DILocation(line: 39, column: 16, scope: !47)
!61 = !DILocation(line: 39, column: 5, scope: !47)
!62 = !DILocation(line: 40, column: 10, scope: !63)
!63 = distinct !DILexicalBlock(scope: !47, file: !6, line: 40, column: 9)
!64 = !DILocation(line: 40, column: 9, scope: !47)
!65 = !DILocation(line: 40, column: 22, scope: !63)
!66 = !DILocation(line: 41, column: 5, scope: !47)
