; ModuleID = '/home/klee/log_tmp_preprocessing1/test_annotated.bc'
source_filename = "/home/klee/log_tmp_preprocessing1/test_annotated.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str = private unnamed_addr constant [6 x i8] c"input\00", align 1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @logic_bomb(i8* %s) #0 !dbg !9 {
entry:
  %retval = alloca i32, align 4
  %s.addr = alloca i8*, align 8
  %symvar = alloca i32, align 4
  %d = alloca double, align 8
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !16, metadata !DIExpression()), !dbg !17
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !18, metadata !DIExpression()), !dbg !19
  %0 = load i8*, i8** %s.addr, align 8, !dbg !20
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !20
  %1 = load i8, i8* %arrayidx, align 1, !dbg !20
  %conv = sext i8 %1 to i32, !dbg !20
  %sub = sub nsw i32 %conv, 48, !dbg !21
  store i32 %sub, i32* %symvar, align 4, !dbg !19
  call void @llvm.dbg.declare(metadata double* %d, metadata !22, metadata !DIExpression()), !dbg !24
  %2 = load i32, i32* %symvar, align 4, !dbg !25
  %conv1 = sitofp i32 %2 to double, !dbg !25
  %call = call double @log(double %conv1) #4, !dbg !26
  store double %call, double* %d, align 8, !dbg !24
  %3 = load double, double* %d, align 8, !dbg !27
  %cmp = fcmp olt double 2.000000e+00, %3, !dbg !29
  %4 = load double, double* %d, align 8
  %cmp3 = fcmp olt double %4, 4.000000e+00
  %or.cond = select i1 %cmp, i1 %cmp3, i1 false, !dbg !30
  br i1 %or.cond, label %if.then, label %if.else, !dbg !30

if.then:                                          ; preds = %entry
  store i32 1, i32* %retval, align 4, !dbg !31
  br label %return, !dbg !31

if.else:                                          ; preds = %entry
  store i32 0, i32* %retval, align 4, !dbg !33
  br label %return, !dbg !33

return:                                           ; preds = %if.else, %if.then
  %5 = load i32, i32* %retval, align 4, !dbg !35
  ret i32 %5, !dbg !35
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

; Function Attrs: nounwind
declare dso_local double @log(double) #2

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main() #0 !dbg !36 {
entry:
  %retval = alloca i32, align 4
  %input = alloca [4 x i8], align 1
  store i32 0, i32* %retval, align 4
  call void @llvm.dbg.declare(metadata [4 x i8]* %input, metadata !39, metadata !DIExpression()), !dbg !43
  %arraydecay = getelementptr inbounds [4 x i8], [4 x i8]* %input, i64 0, i64 0, !dbg !44
  call void @klee_make_symbolic(i8* %arraydecay, i64 4, i8* getelementptr inbounds ([6 x i8], [6 x i8]* @.str, i64 0, i64 0)), !dbg !45
  %arrayidx = getelementptr inbounds [4 x i8], [4 x i8]* %input, i64 0, i64 3, !dbg !46
  %0 = load i8, i8* %arrayidx, align 1, !dbg !46
  %conv = sext i8 %0 to i32, !dbg !46
  %cmp = icmp eq i32 %conv, 0, !dbg !47
  %conv1 = zext i1 %cmp to i32, !dbg !47
  %conv2 = sext i32 %conv1 to i64, !dbg !46
  call void @klee_assume(i64 %conv2), !dbg !48
  %arraydecay3 = getelementptr inbounds [4 x i8], [4 x i8]* %input, i64 0, i64 0, !dbg !49
  %call = call i32 @logic_bomb(i8* %arraydecay3), !dbg !50
  ret i32 0, !dbg !51
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #3

declare dso_local void @klee_assume(i64) #3

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { nounwind }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!3, !4, !5, !6, !7}
!llvm.ident = !{!8}

!0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !1, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !2, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "/home/klee/log_tmp_preprocessing1/test_annotated.c", directory: "/home/klee")
!2 = !{}
!3 = !{i32 7, !"Dwarf Version", i32 4}
!4 = !{i32 2, !"Debug Info Version", i32 3}
!5 = !{i32 1, !"wchar_size", i32 4}
!6 = !{i32 7, !"uwtable", i32 1}
!7 = !{i32 7, !"frame-pointer", i32 2}
!8 = !{!"clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)"}
!9 = distinct !DISubprogram(name: "logic_bomb", scope: !10, file: !10, line: 11, type: !11, scopeLine: 11, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!10 = !DIFile(filename: "log_tmp_preprocessing1/test_annotated.c", directory: "/home/klee")
!11 = !DISubroutineType(types: !12)
!12 = !{!13, !14}
!13 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!14 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !15, size: 64)
!15 = !DIBasicType(name: "char", size: 8, encoding: DW_ATE_signed_char)
!16 = !DILocalVariable(name: "s", arg: 1, scope: !9, file: !10, line: 11, type: !14)
!17 = !DILocation(line: 11, column: 22, scope: !9)
!18 = !DILocalVariable(name: "symvar", scope: !9, file: !10, line: 12, type: !13)
!19 = !DILocation(line: 12, column: 9, scope: !9)
!20 = !DILocation(line: 12, column: 18, scope: !9)
!21 = !DILocation(line: 12, column: 23, scope: !9)
!22 = !DILocalVariable(name: "d", scope: !9, file: !10, line: 13, type: !23)
!23 = !DIBasicType(name: "double", size: 64, encoding: DW_ATE_float)
!24 = !DILocation(line: 13, column: 12, scope: !9)
!25 = !DILocation(line: 13, column: 20, scope: !9)
!26 = !DILocation(line: 13, column: 16, scope: !9)
!27 = !DILocation(line: 14, column: 12, scope: !28)
!28 = distinct !DILexicalBlock(scope: !9, file: !10, line: 14, column: 8)
!29 = !DILocation(line: 14, column: 10, scope: !28)
!30 = !DILocation(line: 14, column: 14, scope: !28)
!31 = !DILocation(line: 15, column: 9, scope: !32)
!32 = distinct !DILexicalBlock(scope: !28, file: !10, line: 14, column: 23)
!33 = !DILocation(line: 17, column: 9, scope: !34)
!34 = distinct !DILexicalBlock(scope: !28, file: !10, line: 16, column: 10)
!35 = !DILocation(line: 19, column: 1, scope: !9)
!36 = distinct !DISubprogram(name: "main", scope: !10, file: !10, line: 21, type: !37, scopeLine: 21, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!37 = !DISubroutineType(types: !38)
!38 = !{!13}
!39 = !DILocalVariable(name: "input", scope: !36, file: !10, line: 22, type: !40)
!40 = !DICompositeType(tag: DW_TAG_array_type, baseType: !15, size: 32, elements: !41)
!41 = !{!42}
!42 = !DISubrange(count: 4)
!43 = !DILocation(line: 22, column: 10, scope: !36)
!44 = !DILocation(line: 23, column: 24, scope: !36)
!45 = !DILocation(line: 23, column: 5, scope: !36)
!46 = !DILocation(line: 24, column: 17, scope: !36)
!47 = !DILocation(line: 24, column: 26, scope: !36)
!48 = !DILocation(line: 24, column: 5, scope: !36)
!49 = !DILocation(line: 25, column: 16, scope: !36)
!50 = !DILocation(line: 25, column: 5, scope: !36)
!51 = !DILocation(line: 26, column: 5, scope: !36)
